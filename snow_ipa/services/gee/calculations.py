import ee
import logging

logger = logging.getLogger(__name__)


def snow_cloud_mask(image: ee.Image) -> ee.Image:
    """
    Calculates the Snow Cloud Index (SCI) and Cloud Cover Index (CCI) for an image
    and returns the image with the new SCI and CCI bands attached.

    Expects the image to have two bands:
    - "NDSI_Snow_Cover"
    - "Snow_Albedo_Daily_Tile_Class".

    Parameters:
    -----------
        image (ee.Image): The input image to calculate the SCI and CCI for.

    Returns:
    --------
        ee.Image: The input image with the new SCI and CCI bands attached.

    Notes:
    ------
    The NDSI threshold is set to 40.
    The Snow Albedo Daily Tile Class is set to 150.
    """
    # TODO: Need to check if missing bands raise an error

    NDSI_THRESHOLD = 40
    ee_snow = (
        image.select("NDSI_Snow_Cover").gte(NDSI_THRESHOLD).multiply(100).rename("SCI")  # type: ignore
    )
    ee_cloud = (
        image.select("Snow_Albedo_Daily_Tile_Class").eq(150).multiply(100).rename("CCI")  # type: ignore
    )

    return image.addBands(ee_snow).addBands(ee_cloud)  # type: ignore
