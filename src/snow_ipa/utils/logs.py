import os
import logging
import logging.config
import copy
from snow_ipa.utils.utils import replace_values_in_dict
from snow_ipa.core.configs import (
    DEFAULT_LOGGING_CONFIG,
)

logger = logging.getLogger(DEFAULT_LOGGING_CONFIG["name"])


def get_log_level(log_level: str = "INFO") -> int | None:
    """
    Returns the numerical value of the log level based on the input string.
    Args:
        log_level (str): The desired logging level as a string.
                        Acceptable values are "DEBUG", "INFO", "WARNING", and "ERROR".
                        Defaults to "INFO".
    Returns:
        int: The numerical value of the log level or None if the input is invalid.
    """
    log_level = log_level.strip().upper()
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        log_level = "INFO"

    ## Get numerical value of log level.
    num_log_level = getattr(logging, log_level, None)
    return num_log_level


def init_logging_config(config: dict | None = None) -> logging.Logger:
    """
    Initialize the logging configuration for the application.
    This function sets up the logging configuration based on the default settings.
    It configures the logging format, date format, and log file location.
    """

    runtime_log_config = copy.deepcopy(DEFAULT_LOGGING_CONFIG)

    if config:
        runtime_log_config = replace_values_in_dict(
            d=runtime_log_config, replacements=config
        )

    new_logger = logging.getLogger(runtime_log_config["name"])
    new_logger.setLevel(runtime_log_config["log_level"])

    # Formatters
    formatter = logging.Formatter(
        fmt=runtime_log_config["format"], datefmt=runtime_log_config["date_format"]
    )

    # Remove all existing handlers to avoid errors when running in jupyter notebook.
    # print("Removing console logger")
    # print(new_logger.handlers)
    for handler in new_logger.handlers[::-1]:
        new_logger.removeHandler(handler)
    # print(new_logger.handlers)

    # File handler
    fh = logging.FileHandler(
        runtime_log_config["log_file"], encoding=runtime_log_config["encoding"]
    )
    fh.setLevel(runtime_log_config["log_level"])
    fh.setFormatter(formatter)
    new_logger.addHandler(fh)

    # Console handler. Only if running in container to log to stdout/stderr
    if os.getenv("SNOW_CONTAINERIZED", "false").lower() in ["true", "1", "yes"]:
        ch = logging.StreamHandler()
        ch.setLevel(runtime_log_config["log_level"])
        ch.setFormatter(formatter)
        new_logger.addHandler(ch)

    # print(new_logger.handlers)

    # logging_config = update_logging_config(config)
    # logging.config.dictConfig(logging_config)
    # return logging.getLogger(LOGGER_NAME)
    return new_logger
