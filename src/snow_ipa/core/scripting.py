import logging
import pprint
from datetime import datetime
from copy import deepcopy

from snow_ipa.services.messaging import EmailService, parse_emails, send_error_message
from email_validator import validate_email, EmailNotValidError
from snow_ipa.utils import utils, dates
from snow_ipa.core.configs import (
    DEFAULT_CONFIG,
    PRIVATE_CONFIGS,
    REQUIRED_EMAIL_CONFIGS,
)
from snow_ipa.core.command_line import set_argument_parser

logger = logging.getLogger(__name__)

# TODO: Verify all months_to_save are in format YYYY-MM-01
# TODO: Confirm dates from MODIS, GEE and GDRIVE are properly sorted


class ScriptManager:
    """
    A class to manage configuration-related tasks, including environment variables,
    command-line arguments, and validation.
    """

    export_to_gee: bool = False
    export_to_gdrive: bool = False

    def __init__(self, new_config: dict | None = None) -> None:
        self.start_time: datetime = datetime.now()
        self.config: dict = deepcopy(DEFAULT_CONFIG)
        self.email_service: EmailService | None = None
        self.status: str = "OK"

        self.update_config(new_config)
        if self.config["export_to"] in ["toAsset", "toAssetAndDrive"]:
            self.export_to_gee = True
        if self.config["export_to"] in ["toDrive", "toAssetAndDrive"]:
            self.export_to_gdrive = True

    def update_config(self, new_config: dict | None = None) -> dict:
        """
        Updates the configuration dictionary with values from a new dictionary.
        """

        if new_config is None:
            return self.config
        new_config = utils.keys_to_lower(new_config)
        self.config = utils.replace_values_in_dict(self.config, new_config)
        return self.config

    def fill_from_files(self) -> None:
        """
        Reads values from files and updates the configuration dictionary.

        Executes for all keys in the configuration dictionary that end with "_file"
        for example "username_file" will be read from the specified file and the read value
        will be set to "username".
        """
        for key, value in self.config.items():
            if key in ["service_credentials_file", "log_file"]:
                continue
            if key.lower().endswith("_file") and value is not None:
                patch_key = key[:-5]
                with open(value, "r") as f:
                    self.config[patch_key] = f.read().strip()

    def check_required(self):
        """
        Check if all the required parameters are provided in the configuration dictionary.
        """
        logger.debug("---Verifying required configuration")

        if self.config["service_credentials_file"] is None:
            raise ValueError("Service credentials file is required.")

        if self.config["export_to"] in ["toAsset", "toAssetAndDrive"]:
            if self.config["gee_assets_path"] is None:
                raise ValueError(
                    "Assets path is required if export_to is set to 'toAsset' or 'toAssetAndDrive'."
                )

        if self.config["export_to"] in ["toDrive", "toAssetAndDrive"]:
            if self.config["gdrive_assets_path"] is None:
                raise ValueError(
                    "Google Drive path is required if export_to is set to 'toDrive' or 'toAssetAndDrive'."
                )

        if self.config["regions_asset_path"] is None:
            raise ValueError("Regions asset path is required.")

        if self.config["months_list"]:
            if not dates.check_valid_date_list(self.config["months_list"]):
                raise ValueError(
                    "One or more dates provided in months_list are not valid"
                )

        logger.debug("---Required configuration verified")
        return True

    def check_email_required(self) -> None:
        """
        Validates the email configuration parameters in the `self.config` dictionary.

        Checks all parameters are present and from and to addresses are valid. This will
        attempt to keep any valid to addresses and will only raise an error in the case
        that none are valid.

        Raises:
            ValueError: If any required email configuration is missing or invalid.
            EmailNotValidError: If the email address is not valid.
        """
        logger.debug("---Verifying email configuration")
        for key in REQUIRED_EMAIL_CONFIGS:
            if self.config[key] is None:
                raise ValueError(f"{key} is required when email is enabled.")

        validated_from_address = validate_email(
            self.config["smtp_from_address"], check_deliverability=False
        )
        validated_from_address = validated_from_address.normalized

        validated_to_address = parse_emails(self.config["smtp_to_address"])
        self.config["smtp_to_address"] = validated_to_address

        if not validated_to_address:
            raise EmailNotValidError("No valid emails found in TO_ADDRESS")

        logger.debug("---Email configuration verified")

    def run_complete_config(self) -> None:
        # TODO: Attempt to send error message
        # Log the configuration
        logger.debug("---config values:")
        logger.debug(self.print_config())

        self.fill_from_files()
        try:
            # Attempting to initialize email service first to send error
            if self.config["enable_email"]:
                self.check_email_required()
                logger.debug("---Initializing email messaging")
                self.email_service = EmailService(
                    smtp_server=self.config["smtp_server"],
                    smtp_port=self.config["smtp_port"],
                    smtp_username=self.config["smtp_username"],
                    smtp_password=self.config["smtp_password"],
                )
                logger.debug("Email messaging enabled")
            else:
                self.email_service = None
                logger.debug("Email messaging disabled")
            self.check_required()
        except Exception as e:
            self.status = "ERROR"
            logger.error(f"Configuration failed: {str(e)}")

            # Attempt to send error by email
            if self.email_service:
                pass
                # terminate_error(
                #     err_message=f"Configuration failed: {str(e)}",
                #     script_start_time=self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                #     exception=e,
                #     email_service=self.email_service,
                #     exit_script=False,
                # )
            raise e

    def print_config(self, keys_to_mask: list = []) -> str:
        """
        Masks specific values in the configuration and prints it using pprint.
        """
        keys_to_mask = PRIVATE_CONFIGS + keys_to_mask
        masked_data = self.config.copy()
        for key in keys_to_mask:
            if key in masked_data:
                masked_data[key] = "********"
        return pprint.pformat(masked_data, width=1)


def init_script_config() -> ScriptManager:
    parser = set_argument_parser()
    args = parser.parse_args(args=[])
    runtime_config = ScriptManager(vars(args))
    return runtime_config


def error_message(e: Exception, script_manager: ScriptManager) -> None:
    """
    Generates an error message for the given exception.

    Args:
        e (Exception): The exception to generate the error message for.
        script_manager (ScriptManager): The script manager instance.
    """
    if script_manager.email_service:
        logger.exception(e)
        logger.debug("Sending error message via email")
        send_error_message(
            script_start_time=script_manager.start_time,
            exception=e,
            email_service=script_manager.email_service,
            from_address=script_manager.config["smtp_from_address"],
            to_address=script_manager.config["smtp_to_address"],
        )
