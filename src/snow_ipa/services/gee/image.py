from ee.image import Image
from ee.feature import Feature
import logging

logger = logging.getLogger(__name__)


def get_date_ymd(image: Image):
    """
    Returns a feature with the date of the given image in the format "YYYY-MM-dd".

    Args:
        image (Image): The image to get the date from.

    Returns:
        ee.Feature: A feature with the date of the given image.
    """
    return Feature(None, {"date": image.date().format("YYYY-MM-dd")})  # type: ignore
