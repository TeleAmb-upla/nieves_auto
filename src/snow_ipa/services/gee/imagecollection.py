import logging
from datetime import datetime, timedelta, date
from ee.imagecollection import ImageCollection
from ee import ee_date, ee_list
from snow_ipa.utils import dates
from snow_ipa.services.gee import dates as gee_dates
from snow_ipa.core.scripting import DEFAULT_CONFIG
from snow_ipa.core.configs import MODIS
from snow_ipa.services.gee.image import get_date_ymd

logger = logging.getLogger(__name__)

# tODO: improve monthly mean function to avoid for loops.


def ic_rm_incomplete_months(
    collection: ImageCollection,
    last_expected_img_dt: date = dates.prev_month_last_date(),
) -> ImageCollection:
    """
    Removes last months from an image collection if they don't have all the images for the month. Meaning, it is \'incomplete\'.
    The month is considered incomplete if the image of the last day of the month is not present.

    Args:
        collection: an Image collection
        last_expected_img_dt: date of the last expected image in a collection.

    Returns: an ImageCollection
    """
    try:
        # Get the date of the last image in the collection
        last_image_dt = ee_date.Date(
            collection.sort(prop="system:time_start", opt_ascending=False)
            .first()
            .get("system:time_start")  # type: ignore
        ).getInfo()
    except Exception as e:
        logger.error("Couldn't get image date from GEE")
        raise
    try:
        # Copy date of last image from server
        if last_image_dt is not None:
            last_image_dt = gee_dates.eedate_to_datetime(last_image_dt).date()
    except Exception as e:
        logger.error("Couldn't format image date from GEE")

    try:
        # Remove the last month if last image != last expected image
        if last_image_dt != last_expected_img_dt:
            incomplete_month = (
                f"{last_expected_img_dt.year}-{last_expected_img_dt.month}"
            )
            msg = f"Removing Incomplete month {incomplete_month} from collection..."
            # print(msg)
            logger.info(msg)
            logger.debug(f"\t Last Image Expected: {last_expected_img_dt}")
            logger.debug(f"\t Last Image found: {last_image_dt}")
            new_end_date = last_expected_img_dt.replace(day=1)
            new_end_date_ym = f"{new_end_date.year}-{new_end_date.month}"
            collection = collection.filterDate(MODIS["min_month"], new_end_date_ym)
            new_last_month = new_end_date - timedelta(days=1)
            logger.debug(
                f"New last month is: {new_last_month.year}-{new_last_month.month}"
            )
            logger.debug(f"\t New Last Image Expected: {new_last_month}")
            # Recurrent call in case more incomplete months are present
            collection = ic_rm_incomplete_months(
                collection=collection, last_expected_img_dt=new_last_month
            )
        else:
            # Return new image collection if there are no incomplete months to remove
            logger.info(
                f"Last complete month in collection: {last_expected_img_dt.year}-{last_expected_img_dt.month}"
            )
        return collection
    except Exception as e:
        logger.error(
            "Couldn't remove images of incomplete months from image collection."
        )
        logger.error(e)
        raise


def ic_get_distinct_months(collection: ImageCollection) -> list:
    """
    Returns a list of distinct months in an image collection.
    Distinct months are represented by the first day of the month.
    For example, 2000-01-01 represents January, 2000.

    Dates are sorted in descending order.

    Args:
        collection: An ee.ImageCollection object.

    Returns:
        A list of distinct months in the image collection, represented by the first day of the month.
    """

    ee_dates = collection.map(get_date_ymd).distinct("date").aggregate_array("date")  # type: ignore
    collection_dates = ee_dates.getInfo()
    logger.debug(f"Total distinct dates in Imagecollection: {len(collection_dates)}")

    # Filter dates that are not first day of the month
    distinct_months = [date for date in collection_dates if date.endswith("-01")]
    distinct_months.sort(reverse=True)
    logger.debug(f"Distinct months in collection: {len(distinct_months)}")
    logger.debug(f"First month: {distinct_months[len(distinct_months)-1]}")
    logger.debug(f"Last month: {distinct_months[0]}")

    return distinct_months


def ic_monthly_mean(
    months: list | str, imagecollection: ImageCollection
) -> ImageCollection:
    """
    Calculates the monthly mean of an ImageCollection.

    Args:
        months: A list of months in the format YYYY-MM-DD or a string representing a single month in the same format.
        collection: An ImageCollection containing images from one or more months.

    Returns:
        An ImageCollection containing the monthly means.

    Raises:
        TypeError: If the `months` argument is not a list or a string.
        ValueError: If the `months` argument is a string that does not represent a valid date.

    Example:
        # Import the Earth Engine Python Package
        import ee
        ee.Initialize()

        # Define the ImageCollection
        collection = ee.ImageCollection('MODIS/006/MOD11A2').select('LST_Day_1km')

        # Calculate the monthly mean for January 2020
        monthly_mean = ic_monthly_mean('2020-01-01', collection)
    """
    # Check if months is a list, if not convert to list
    if isinstance(months, list):
        pass
    elif isinstance(months, str):
        # If string, check if it's a valid date and convert to list
        try:
            format = "%Y-%m-%d"
            datetime.strptime(months, format)
        except ValueError:
            raise ValueError(
                f"Invalid date format: {months}. Must be in the format YYYY-MM-DD."
            )
        months = [months]
    else:
        raise TypeError(
            f"Invalid argument type: {type(months)}. Must be a list or a string."
        )

    # Initialize an empty list to store the resulting images
    ee_image_list = ee_list.List([])

    # Loop through each month in the list
    for month in months:
        # Get the start date of the target month
        ee_target_ym = ee_date.Date(month)
        ee_target_month = ee_target_ym.get("month")  # type: ignore
        ee_target_year = ee_target_ym.get("year")  # type: ignore

        # Get the end date of the target month
        ee_post_target_ym = ee_target_ym.advance(1, "month")  # type: ignore

        # # Log the processing message
        # logger.debug(
        #     f"Processing: [{gee_dates.eedate_to_datetime(ee_target_ym.getInfo()).date()} - {gee_dates.eedate_to_datetime(ee_post_target_ym.getInfo()).date()}["
        # )

        # Calculate the mean of the images in the collection for the target month
        ee_image = imagecollection.filterDate(ee_target_ym, ee_post_target_ym).mean()  # type: ignore

        # Set the metadata for the resulting image
        ee_image = ee_image.set("month", ee_target_month)
        ee_image = ee_image.set("year", ee_target_year)
        ee_image = ee_image.set("system:time_start", ee_target_ym.format("YYYY-MM"))  # type: ignore

        # Add the resulting image to the list
        ee_image_list = ee_image_list.add(ee_image)  # type: ignore

    # Convert the list to an ImageCollection and return it
    ee_image_collection = ImageCollection(ee_image_list)
    return ee_image_collection
