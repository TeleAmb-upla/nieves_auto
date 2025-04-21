LOGGER_NAME = "snow_ipa"
DEFAULT_LOG_FILE = "./snow.log"
DEFAULT_LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": DEFAULT_LOG_FORMAT,
            "datefmt": DEFAULT_LOG_DATE_FORMAT,
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": DEFAULT_LOG_FILE,
            "encoding": "utf-8",
            "formatter": "standard",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        LOGGER_NAME: {
            "handlers": ["file", "console"],
            "level": "INFO",
        }
    },
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
    "log_level": "INFO",
    "log_file": DEFAULT_LOG_FILE,
    "log_format": DEFAULT_LOG_FORMAT,
    "log_date_format": DEFAULT_LOG_DATE_FORMAT,
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

ERROR_EMAIL_TEMPLATE = "error_email_template.txt"
SUCCESS_EMAIL_TEMPLATE = ""

MODIS = {
    "path": "MODIS/061/MOD10A1",
    "min_month": "2000-03",
}
