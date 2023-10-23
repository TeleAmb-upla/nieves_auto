import argparse
import logging


import argparse


def set_argument_parser() -> argparse.ArgumentParser:
    """
    Creates an argument parser for the command line interface.

    Returns:
        argparse.ArgumentParser: An argument parser object.
    """
    # Create the parser
    parser = argparse.ArgumentParser()

    # Service user
    parser.add_argument(
        "-u", "--service-user", dest="user", help="Service account user ID"
    )

    # Service credentials
    parser.add_argument(
        "-c",
        "--service-credentials",
        dest="service_credentials_file",
        help="Service account credentials file location",
    )

    # GEE Asset Path where images will be saved
    parser.add_argument(
        "-s",
        "--assets-path",
        dest="assets_path",
        help="GEE asset path for saving images",
    )

    # Google Drive Path where images will be saved
    parser.add_argument(
        "-d",
        "--drive-path",
        dest="drive_path",
        help="Google Drive path for saving images",
    )

    # GEE Asset Path for reading regions FeatureCollection
    parser.add_argument(
        "-r",
        "--regions-asset-path",
        dest="regions_asset_path",
        help="GEE asset path for reading regions FeatureCollection",
    )

    # Options for exporting images
    parser.add_argument(
        "-e",
        "--export-to",
        dest="export_to",
        help="Where to export images. Valid options [toAsset | toDrive | toAssetAndDrive]. Default=toAsset ",
        choices=["toAsset", "toDrive", "toAssetAndDrive"],
    )

    # Time period arguments
    parser.add_argument(
        # "-m",
        "--months-to-export",
        dest="months_list",
        help="string of months to export '2022-11-01, 2022-10-01'. Default is to export the last fully available month in MODIS",
    )

    # Logging arguments
    parser.add_argument(
        "-l",
        "--log-level",
        dest="log_level",
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    # Enable email notifications
    parser.add_argument(
        "--enable-email",
        dest="enable_email",
        help="Enable email notifications",
        action="store_true",
    )

    # Email arguments
    parser.add_argument(
        "--smtp-server",
        dest="smtp_server",
        help="SMTP server for sending email",
    )

    parser.add_argument(
        "--smtp-port",
        dest="smtp_port",
        help="SMTP port for sending email",
    )

    parser.add_argument(
        "--smtp-user",
        dest="smtp_username",
        help="SMTP user for connecting to server",
    )

    parser.add_argument(
        "--smtp-password",
        dest="smtp_password",
        help="SMTP password for connecting to server",
    )

    parser.add_argument(
        "--smtp-user-file",
        dest="smtp_username_file",
        help="file with SMTP user for connecting to server",
    )

    parser.add_argument(
        "--smtp-password-file",
        dest="smtp_password_file",
        help="file with SMTP password for connecting to server",
    )

    parser.add_argument(
        "--from-address",
        dest="from_address",
        help="From email address for sending email",
    )

    parser.add_argument(
        "--to-address",
        dest="to_address",
        help="Comma-separated list of email addresses to send email to",
    )

    return parser


def main() -> None:
    pass


if __name__ == "__main__":
    main()
