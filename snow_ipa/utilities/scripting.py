import os
import sys
import logging
import pprint
from typing import Optional
from datetime import datetime

from .messaging import EmailSender
from .logs import print_log

# from command_line import set_argument_parser

# Default values for the script
DEFAULT_CONFIG = {
    "SERVICE_USER": None,
    "SERVICE_CREDENTIALS_FILE": None,
    "EXPORT_TO": "toAsset",
    "ASSETS_PATH": None,
    "DRIVE_PATH": None,
    "REGIONS_ASSET_PATH": None,
    "MONTHS_LIST": None,
    "ENABLE_EMAIL": False,
    "SMTP_SERVER": None,
    "SMTP_PORT": None,
    "SMTP_USERNAME": None,
    "SMTP_PASSWORD": None,
    "SMTP_USERNAME_FILE": None,
    "SMTP_PASSWORD_FILE": None,
    "FROM_ADDRESS": None,
    "TO_ADDRESS": None,
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "./snow.log",
    "LOG_FORMAT": "%(asctime)s %(name)s %(levelname)s: %(message)s",
    "LOG_DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
    "STATUS_CHECK_WAIT": 30,
    "MAX_EXPORTS": 10,
    "MODIS_MIN_MONTH": "2000-03",
}

PRIVATE_CONFIGS = ["SMTP_PASSWORD"]

REQUIRED_CONFIGS = ["SERVICE_CREDENTIALS_FILE", "REGIONS_ASSET_PATH"]

REQUIRED_EMAIL_CONFIGS = ["SMTP_SERVER", "SMTP_PORT", "FROM_ADDRESS", "TO_ADDRESS"]


def init_config(
    config: dict, cmd_args: dict | None = None, env_prefix: str = "SNOW"
) -> dict:
    """
    Initializes a configuration dictionary with default values.
    If environment variables are set for any of the keys, those values will be used instead.
    If cmd_args is provided, any keys in the configuration that match a key in cmd_args (case-insensitive) will be updated with the corresponding value from cmd_args.

    Args:
        config (dict): A dictionary containing default configuration values.
        cmd_args (dict, optional): A dictionary containing command-line arguments. Defaults to None.

    Returns:
        dict: A dictionary containing the final configuration values.
    """
    target_config = {}

    # Replace default values with environment variables
    for key in config:
        target_config[key] = config[key]
        env_key = f"{env_prefix}_{key}"
        env_value = os.environ.get(env_key, None)
        # Strip quotes from Environment Variables
        env_value = env_value.strip(" \"'") if env_value else None
        if env_value:
            target_config[key] = env_value

    # Replace values with command-line arguments
    if cmd_args:
        for key in target_config:
            try:
                cmd_value = cmd_args[key.lower()]
            except KeyError:
                continue
            if cmd_value:
                target_config[key] = cmd_value

    # Parse list values from comma-separated strings if key ends with "_LIST"
    for key in target_config:
        if key.endswith("_LIST") and target_config[key] is not None:
            try:
                target_config[key] = csv_to_list(target_config[key])
            except Exception as e:
                logging.error(f"Error parsing {key}: {e}")
                raise

    # Show final value in log
    return target_config


def csv_to_list(csv_string: str) -> list:
    """
    Converts a comma-separated string to a list of strings.

    Args:
        csv_string: A string of comma-separated values.

    Returns:
        A list of strings.
    """
    csv_list = [item.strip(" \"'") for item in csv_string.split(",")]

    # Remove empty strings from list
    csv_list = list(filter(None, csv_list))
    return csv_list


def check_required(config):
    """
    Check if all the required parameters are provided in the configuration dictionary.

    Args:
        config (dict): A dictionary containing the configuration parameters.

    Raises:
        Exception: If any of the required parameters is missing.

    Returns:
        bool: True if all the required parameters are provided, False otherwise.
    """
    # check service credentials are provided
    if config["SERVICE_CREDENTIALS_FILE"] is None:
        raise Exception("Service credentials file is required.")

    # check asset or drive path are provided depending on the value of EXPORT_TO
    if config["EXPORT_TO"] in ["toAsset", "toAssetAndDrive"]:
        if config["ASSETS_PATH"] is None:
            raise Exception("Assets path is required.")

    if config["EXPORT_TO"] in ["toDrive", "toAssetAndDrive"]:
        if config["DRIVE_PATH"] is None:
            raise Exception("Drive path is required.")

    # check regions asset path is provided
    if config["REGIONS_ASSET_PATH"] is None:
        raise Exception("Regions asset path is required.")

    # check email config data is provided if email is enabled
    # user can provide username and password or files containing them
    if config["ENABLE_EMAIL"]:
        if config["SMTP_SERVER"] is None:
            raise Exception("SMTP server is required.")
        if config["SMTP_PORT"] is None:
            raise Exception("SMTP port is required.")
        if config["FROM_ADDRESS"] is None:
            raise Exception("From address is required.")
        if config["TO_ADDRESS"] is None:
            raise Exception("To address is required.")
        if config["SMTP_USERNAME"] is None and config["SMTP_USERNAME_FILE"] is None:
            raise Exception("SMTP username is required.")
        if config["SMTP_PASSWORD"] is None and config["SMTP_PASSWORD_FILE"] is None:
            raise Exception("SMTP password is required.")

    return True


def read_file_to_var(file_path: str) -> str:
    """
    Reads a file and returns its contents as a string.

    Args:
        file_path (str): The path to the file to read.

    Returns:
        str: The contents of the file.
    """
    with open(file_path, "r") as f:
        file_contents = f.read()
    return file_contents


def print_config(data: dict, keys_to_mask: list = []) -> str:
    """
    Masks specific values in a dictionary and prints it using pprint.

    Args:
        data (dict): The dictionary to mask and print.
        keys_to_mask (list): A list of keys whose values should be masked.
    """
    # Join private configs with keys_to_mask
    keys_to_mask = PRIVATE_CONFIGS + keys_to_mask

    masked_data = data.copy()
    for key in keys_to_mask:
        if key in masked_data:
            masked_data[key] = "********"

    return pprint.pformat(masked_data, width=1)


def get_email_template(template_path: str, default_template: str) -> str:
    try:
        with open(template_path) as file:
            return file.read()
    except FileNotFoundError:
        return default_template


def terminate_error(
    err_message: str,
    script_start_time: str,
    exception_traceback: Exception | None = None,
    email_service: EmailSender | None = None,
    exit_script: bool = False,
) -> None:
    """
    Terminate the script execution due to an error and writes to log file.

    If an EmailSender object is provided, an email with the error details will be sent to
    the emails provided to the object.

    Args:
        err_message (str): The error message describing the cause of the termination.
        script_start_time (str): The start time of the script execution.
        exception_traceback (Exception | None): An optional Exception object containing the traceback of the error. Defaults to None.,
        email_service (EmailSender | None): An optional EmailSender object for sending error emails. Defaults to None.

    Returns:
        None

    Raises:
        SystemExit: This function terminates the script execution using sys.exit().

    """
    script_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Email
    if email_service is not None:
        template_path = "./templates/error_email_template"
        default_template = "Error Message: [error_message]"
        template = get_email_template(template_path, default_template)

        # Update template
        message = template.replace("[error_message]", err_message)
        message = message.replace("[start_time]", script_start_time)
        message = message.replace("[end_time]", script_end_time)

        subject = "Snow Image Processing Automation"
        email_service.send_email(subject=subject, body=message)

    # Logging
    if exception_traceback:
        logging.error(str(exception_traceback))
    print_log(err_message, "ERROR")
    logging.info("------ EXITING SCRIPT ------")

    # terminate
    if exit_script:
        sys.exit()
