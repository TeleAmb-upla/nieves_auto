DEFAULT_LOGGING_CONFIG = {
    "name": "snow_ipa",
    "log_file": "./snow.log",
    "log_level": "INFO",
    "encoding": "utf-8",
    "format": "%(asctime)s %(name)s %(levelname)s: %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
}

DEFAULT_CONFIG = {
    "user": None,
    "service_credentials_file": None,
    "export_to": "toAsset",
    "gee_assets_path": None,
    "gdrive_assets_path": None,
    "regions_asset_path": None,
    "months_list": None,
    "enable_email": False,
    "smtp_server": None,
    "smtp_port": None,
    "smtp_username": None,
    "smtp_password": None,
    "smtp_username_file": None,
    "smtp_password_file": None,
    "smtp_from_address": None,
    "smtp_to_address": None,
    "log_level": DEFAULT_LOGGING_CONFIG["log_level"],
    "log_file": DEFAULT_LOGGING_CONFIG["log_file"],
    "log_format": DEFAULT_LOGGING_CONFIG["format"],
    "log_date_format": DEFAULT_LOGGING_CONFIG["date_format"],
    "status_check_wait": 30,
    "max_exports": 10,
    "modis_min_month": "2000-03",
}

PRIVATE_CONFIGS = ["smtp_password"]
REQUIRED_CONFIGS = ["service_credentials_file", "regions_asset_path"]
REQUIRED_EMAIL_CONFIGS = [
    "smtp_server",
    "smtp_port",
    "smtp_username",
    "smtp_password",
    "smtp_from_address",
    "smtp_to_address",
]

ERROR_TXT_EMAIL_TEMPLATE = "error_email_template.txt"
ERROR_HTML_EMAIL_TEMPLATE = "error_email_template.html"
SUCCESS_EMAIL_TEMPLATE = "report_email_template.txt"
REPORT_TXT_EMAIL_TEMPLATE = "report_email_template.txt"
REPORT_HTML_EMAIL_TEMPLATE = "report_email_template.html"

MODIS = {
    "path": "MODIS/061/MOD10A1",
    "min_month": "2000-03",
}
