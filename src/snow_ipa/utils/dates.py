from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def check_valid_date(date_string: str) -> bool:
    """
    Checks if a string is a valid date format.

    Args:
        date_string: String that represents a date

    Returns:
        Returns TRUE if the string has a valid date format
    """
    try:
        valid_date = date.fromisoformat(date_string)
        return True
    except Exception as e:
        logger.warning(e)
        return False


def check_valid_date_list(date_list: list | str) -> bool:
    """
    Checks if a list of strings only has valid date formats. Returns false if at least one of of the items in the list has an invalid format.

    Args:
        date_list: list of strings representing dates

    Returns:
        Returns TRUE if all the stings in the list are valid dates
    """
    if type(date_list) is str:
        date_list = [date_list]

    return all(map(check_valid_date, date_list))


def current_year_month() -> str:
    """
    Returns the current year and month from local machine time as a string
    e.g. 2022-12
    """
    return str(datetime.today().year) + "-" + str(datetime.today().month)


def prev_month_last_date() -> date:
    """
    Returns the last day of the previous month relative to the current date
    Current date is taken from datetime.today()

    Returns:
        Returns a datetime.date object
    """
    return datetime.today().date().replace(day=1) - timedelta(days=1)
