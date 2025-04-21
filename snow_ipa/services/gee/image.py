import ee
import logging

logger = logging.getLogger(__name__)


def get_date_ymd(image: ee.Image):
    """
    Returns a feature with the date of the given image in the format "YYYY-MM-dd".

    Args:
        image (ee.Image): The image to get the date from.

    Returns:
        ee.Feature: A feature with the date of the given image.
    """
    return ee.Feature(None, {"date": image.date().format("YYYY-MM-dd")})  # type: ignore
