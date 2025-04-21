import logging
import logging.config
import copy
from snow_ipa.utils.utils import replace_values_in_dict
from snow_ipa.core.configs import DEFAULT_LOGGING_CONFIG, LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


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


def update_logging_config(config: dict | None = None) -> dict:
    """
    Update the default logging configuration with the provided configuration.
    Args:
        config (dict): A dictionary containing the configuration values.
    Returns:
        dict: A dictionary containing the updated logging configuration.
    """
    runtime_config = copy.deepcopy(DEFAULT_LOGGING_CONFIG)

    config_options = {
        "log_level": None,
        "log_file": None,
    }

    if config:
        config_options = replace_values_in_dict(d=config_options, replacements=config)

    if config_options["log_level"]:
        runtime_config["loggers"][LOGGER_NAME]["level"] = config_options["log_level"]

    if config_options["log_file"]:
        runtime_config["handlers"]["file"]["filename"] = config_options["log_file"]

    return runtime_config.copy()


def init_logging_config(config: dict | None = None) -> logging.Logger:
    """
    Initialize the logging configuration for the application.
    This function sets up the logging configuration based on the default settings.
    It configures the logging format, date format, and log file location.
    """
    logging_config = update_logging_config(config)
    logging.config.dictConfig(logging_config)
    return logging.getLogger(LOGGER_NAME)


def print_and_log(message: str, log_level: str = "INFO") -> None:
    """
    Print a message to console and to log file
    If no log file is set, logging will also print to console

    Args:
        message: Message to log
        log_level: log level to use when logging the message. Valid options are DEBUG, INFO, WARNING, ERROR.

    Returns:
        None
    """
    print(message)
    match log_level.upper():
        case "DEBUG":
            logger.debug(message)
        case "INFO":
            logger.info(message)
        case "WARNING":
            logger.warning(message)
        case "ERROR":
            logger.error(message)
