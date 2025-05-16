# libraries
from datetime import datetime, date
import logging
import pytz

logger = logging.getLogger(__name__)

# Constants. Used as Defaults in case no alternative is provided.
UTC_TZ = pytz.timezone("UTC")


def eedate_to_datetime(dt: dict | int, tz=UTC_TZ) -> datetime:
    """
    Formats a date retrieved from GEE using a given timezone.
    Default timezone is UTC
    """
    if isinstance(dt, dict):
        dt = int(dt["value"])
    return datetime.fromtimestamp(dt / 1000, tz)


def print_ee_timestamp(dt: dict | int, tz=UTC_TZ) -> None:
    """
    Prints a date retrieved from GEE using a given Timezone.
    Default timezone is UTC
    """
    print(eedate_to_datetime(dt, tz))
