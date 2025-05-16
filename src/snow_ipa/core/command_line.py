import argparse
import os
from snow_ipa.core.configs import DEFAULT_CONFIG


# NOTE: Some arguments are required but not forcing it since they can also be read from environment variables


def parse_list_arg(value: str) -> list:
    """
    Parse a comma-separated string into a list
    """
    return [item.strip().strip("'\"") for item in value.split(",")]


def set_argument_parser() -> argparse.ArgumentParser:
    """
    Creates an argument parser for the command line interface.

    Returns:
        argparse.ArgumentParser: An argument parser object.
    """
    # Create the parser
    parser = argparse.ArgumentParser(description="Snow Image Processing Automation")

    # Service user - REQUIRED
    parser.add_argument(
        "-u",
        "--user",
        dest="user",
        default=os.getenv("SNOW_USER"),
        type=str,
        help="User or Service account account ID. Can also be set using the SNOW_USER environment variable",
    )

    # Service credentials - REQUIRED
    parser.add_argument(
        "-c",
        "--service-credentials",
        dest="service_credentials_file",
        default=os.getenv("SNOW_SERVICE_CREDENTIALS_FILE"),
        type=str,
        help="Service account credentials file location",
    )

    # GEE Asset Path where images will be saved - CONDITIONALLY REQUIRED
    parser.add_argument(
        "-s",
        "--gee-assets-path",
        dest="gee_assets_path",
        default=os.getenv("SNOW_GEE_ASSETS_PATH"),
        type=str,
        help="GEE asset path where images will be saved",
    )

    # Google Drive Path where images will be saved - CONDITIONALLY REQUIRED
    parser.add_argument(
        "-d",
        "--gdrive-assets-path",
        dest="gdrive_assets_path",
        default=os.getenv("SNOW_GDRIVE_ASSETS_PATH"),
        type=str,
        help="Google Drive path where images will be saved",
    )

    # GEE Asset Path for reading regions FeatureCollection - REQUIRED
    parser.add_argument(
        "-r",
        "--regions-asset-path",
        dest="regions_asset_path",
        default=os.getenv("SNOW_REGIONS_ASSET_PATH"),
        type=str,
        help="GEE asset path for reading regions FeatureCollection",
    )

    # Options for exporting images - OPTIONAL, HAS DEFAULT VALUE
    valid_export_to = ["toAsset", "toDrive", "toAssetAndDrive"]
    default_export_to = os.getenv("SNOW_EXPORT_TO", DEFAULT_CONFIG["export_to"])
    if default_export_to not in valid_export_to:
        raise SystemExit(
            f"Invalid export option specified. Valid options are: {', '.join(valid_export_to)}."
        )

    parser.add_argument(
        "-e",
        "--export-to",
        dest="export_to",
        default=os.getenv("SNOW_EXPORT_TO", DEFAULT_CONFIG["export_to"]),
        choices=valid_export_to,
        type=str,
        help=f"Where to export images. Valid options {', '.join(valid_export_to)}. Default={DEFAULT_CONFIG['export_to']} ",
    )

    # Time period arguments - OPTIONAL

    parser.add_argument(
        "--months-to-export",
        dest="months_list",
        default=os.getenv("SNOW_MONTHS_LIST"),
        type=parse_list_arg,
        help="Comma-separated list of months to export in the format 'YYYY-MM-DD, YYYY-MM-DD'. Default is to export the last fully available month in MODIS.",
    )

    # Logging arguments - OPTIONAL
    # Set default log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    default_log_level = os.getenv("SNOW_LOG_LEVEL", DEFAULT_CONFIG["log_level"])
    if default_log_level not in valid_log_levels:
        raise SystemExit(
            f"Invalid log level specified. Valid options are: {', '.join(valid_log_levels)}."
        )

    parser.add_argument(
        "-l",
        "--log-level",
        dest="log_level",
        default=default_log_level,
        choices=valid_log_levels,
        type=str,
        help=f"Logging level. Valid options are: {', '.join(valid_log_levels)} (Default={DEFAULT_CONFIG['log_level']})",
    )

    parser.add_argument(
        "--log-file",
        dest="log_file",
        default=os.getenv("SNOW_LOG_FILE"),
        type=str,
        help="Alternative log file path",
    )

    # Enable email notifications - OPTIONAL
    parser.add_argument(
        "--enable-email",
        dest="enable_email",
        default=os.getenv("SNOW_ENABLE_EMAIL", "false").lower().strip("'\"")
        in ("true", "1", "yes"),
        action="store_true",
        help="Enable email notifications",
    )

    # Email arguments - CONDITIONALLY REQUIRED
    parser.add_argument(
        "--smtp-server",
        dest="smtp_server",
        default=os.getenv("SNOW_SMTP_SERVER"),
        type=str,
        help="SMTP server for sending email",
    )

    parser.add_argument(
        "--smtp-port",
        dest="smtp_port",
        default=os.getenv("SNOW_SMTP_PORT"),
        type=int,
        help="SMTP port for sending email",
    )

    parser.add_argument(
        "--smtp-user",
        dest="smtp_username",
        default=os.getenv("SNOW_SMTP_USER"),
        type=str,
        help="SMTP user for connecting to server",
    )

    parser.add_argument(
        "--smtp-password",
        dest="smtp_password",
        default=os.getenv("SNOW_SMTP_PASSWORD"),
        type=str,
        help="SMTP password for connecting to server",
    )

    parser.add_argument(
        "--smtp-user-file",
        dest="smtp_username_file",
        default=os.getenv("SNOW_SMTP_USER_FILE"),
        type=str,
        help="file with SMTP user for connecting to server",
    )

    parser.add_argument(
        "--smtp-password-file",
        dest="smtp_password_file",
        default=os.getenv("SNOW_SMTP_PASSWORD_FILE"),
        type=str,
        help="file with SMTP password for connecting to server",
    )

    parser.add_argument(
        "--smtp-from-address",
        dest="smtp_from_address",
        default=os.getenv("SNOW_SMTP_FROM_ADDRESS"),
        type=str,
        help="From email address for sending email",
    )

    parser.add_argument(
        "--smtp-to-address",
        dest="smtp_to_address",
        default=os.getenv("SNOW_SMTP_TO_ADDRESS"),
        type=parse_list_arg,
        help="Comma-separated list of email addresses to send email to",
    )

    return parser
