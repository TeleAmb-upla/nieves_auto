import logging


def log_level_setup(log_level: str = "INFO") -> None:
    log_level = log_level.upper()
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        log_level = "INFO"

    ## Get numerical value of log level.
    num_log_level = getattr(logging, log_level, None)
    return num_log_level


def print_log(message: str, log_level: str = "INFO") -> None:
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
            logging.debug(message)
        case "INFO":
            logging.info(message)
        case "WARNING":
            logging.warning(message)
        case "ERROR":
            logging.error(message)
