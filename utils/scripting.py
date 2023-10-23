from ast import Dict
from calendar import month
from http import server
import os
import logging
from typing import Optional
import pprint

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
    "LOG_FORMAT": "%(asctime)s %(levelname)s %(message)s",
    "LOG_DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
    "STATUS_CHECK_WAIT": 30,
    "MAX_EXPORTS": 10,
    "MODIS_MIN_MONTH": "2000-03",
}

PRIVATE_CONFIGS = ["SMTP_PASSWORD"]


def init_config(DEFAULT_CONFIG, cmd_args=None):
    """
    Initializes a configuration dictionary with default values.
    If environment variables are set for any of the keys, those values will be used instead.
    If cmd_args is provided, any keys in the configuration that match a key in cmd_args (case-insensitive) will be updated with the corresponding value from cmd_args.

    Args:
        DEFAULT_CONFIG (dict): A dictionary containing default configuration values.
        cmd_args (dict, optional): A dictionary containing command-line arguments. Defaults to None.

    Returns:
        dict: A dictionary containing the final configuration values.
    """
    config = {}

    # Replace default values with environment variables
    for key in DEFAULT_CONFIG:
        config[key] = DEFAULT_CONFIG[key]
        env_value = os.environ.get(key, None)
        # Strip quotes from Environment Variables
        env_value = env_value.strip(" \"'") if env_value else None
        if env_value:
            config[key] = env_value

    # Replace values with command-line arguments
    if cmd_args:
        for key in config:
            try:
                cmd_value = cmd_args[key.lower()]
            except KeyError:
                continue
            if cmd_value:
                config[key] = cmd_value

    # Parse list values from comma-separated strings if key ends with "_LIST"
    for key in config:
        if key.endswith("_LIST") and config[key] is not None:
            try:
                config[key] = csv_to_list(config[key])
            except Exception as e:
                logging.error(f"Error parsing {key}: {e}")
                raise

    # Show final value in log
    return config


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


def main():
    # test_set_config()
    pass


if __name__ == "__main__":
    main()
