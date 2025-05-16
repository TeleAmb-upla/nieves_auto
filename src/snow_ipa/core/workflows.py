import logging
import re
from pathlib import Path
import ee
from ee.imagecollection import ImageCollection
from ee.featurecollection import FeatureCollection
from ee import batch

from snow_ipa.core.exporting import ExportManager
from snow_ipa.services.gee import (
    assets as gee_assets,
    imagecollection as gee_imagecollection,
    exports,
    calculations,
)
from snow_ipa.services.gdrive import assets as gdrive_assets

logger = logging.getLogger(__name__)

# TODO: Replace constants with config values
# TODO: Set max number of exports


# GEE Assets
def get_gee_saved_assets(export_manager: ExportManager, gee_asset_path: str):
    """
    Updates ExportManager with a list of saved assets in Google Earth Engine (GEE).

    Adds two lists to the ExportManager:
    - `gee_saved_assets`: List of assets with the full image name excluding path.
    - `gee_saved_assets_months`: List of months in the format YYYY-MM-DD

    Args:
        export_manager (ExportManager): The export manager instance.
        gee_asset_path (str): The path to the GEE assets.

    Returns:
        list: List of saved assets in GEE.
    """
    logger.debug(f"--- Checking for images already saved to GEE")
    try:

        gee_saved_assets = gee_assets.get_asset_list(gee_asset_path, "IMAGE")

        # Remove the path from the asset names
        gee_saved_assets = [Path(asset).name for asset in gee_saved_assets]

        # Keep only assets that start with the image prefix and end with YYYY-MM
        if export_manager.image_prefix:
            pattern = rf"^{export_manager.image_prefix}_(\d{{4}})-(\d{{2}})"
        else:
            pattern = r".*_(\d{4})-(\d{2})"
        gee_saved_assets = [
            image for image in gee_saved_assets if re.fullmatch(pattern, image)
        ]

        # Get list of months from assets names and sort
        gee_saved_assets_months = gee_assets.get_trailing_ym(gee_saved_assets)
        gee_saved_assets_months = [month + "-01" for month in gee_saved_assets_months]

        # Summarize Results
        logger.debug(
            f"Total images saved in GEE Asset folder: {len(gee_saved_assets_months)}"
        )
        if len(gee_saved_assets_months) > 0:
            logger.debug(f"first month saved: {gee_saved_assets_months[-1]}")
            logger.debug(f"last month saved: {gee_saved_assets_months[0]}")

        export_manager.gee_saved_assets = gee_saved_assets
        export_manager.gee_saved_assets_months = gee_saved_assets_months

    except Exception as e:
        logger.error(
            f"Error occurred while checking saved GEE assets: {e}", exc_info=True
        )
        raise e


# Google Drive
def get_gdrive_saved_assets(
    export_manager: ExportManager, gdrive_assets_path: str, gdrive_service
):
    """
    Get the list of saved assets in Google Drive.

    Args:
        export_manager (ExportManager): The export manager instance.
        gdrive_asset_path (str): The path to the Google Drive assets.
        gdrive_service (object): The Google Drive service instance.
    Returns:
        list: List of saved assets in Google Drive.
    """
    logger.debug(f"--- Checking for images already saved to Google Drive")
    try:

        gdrive_saved_assets = gdrive_assets.get_asset_list(
            drive_service=gdrive_service,
            path=gdrive_assets_path,
            asset_type="IMAGE",
        )

        # Keep only assets that start with the image prefix and end with YYYY-MM
        if export_manager.image_prefix:
            pattern = rf"^{export_manager.image_prefix}_(\d{{4}})-(\d{{2}})"
        else:
            pattern = r".*_(\d{4})-(\d{2})"
        gdrive_saved_assets = [
            image for image in gdrive_saved_assets if re.fullmatch(pattern, image)
        ]

        # Get list of months from assets names and sort
        gdrive_saved_assets_months = gee_assets.get_trailing_ym(gdrive_saved_assets)
        gdrive_saved_assets_months = [
            month + "-01" for month in gdrive_saved_assets_months
        ]

        # Summarize Results
        logger.debug(
            f"Total images saved in Google Drive folder: {len(gdrive_saved_assets_months)}"
        )
        if len(gdrive_saved_assets_months) > 0:
            logger.debug(f"first month saved: {gdrive_saved_assets_months[-1]}")
            logger.debug(f"last month saved: {gdrive_saved_assets_months[0]}")

        export_manager.gdrive_saved_assets = gdrive_saved_assets
        export_manager.gdrive_saved_assets_months = gdrive_saved_assets_months

    except Exception as e:
        logger.error(
            f"Error occurred while checking saved GDrive assets: {e}", exc_info=True
        )
        raise e


def target_export_plan(
    export_manager: ExportManager,
    target: str,
    export_plan: list,
    existing_imgs: list,
    image_prefix: str,
):
    target_plan = []
    excluded = []
    for month in export_plan:
        image_name = f"{image_prefix}_{month[:7]}"
        if month in existing_imgs:
            excluded.append(month)
            export_manager.export_tasks.add_task(
                exports.ExportTask(
                    image=image_name,
                    date=month,
                    target=target,
                    status="ALREADY_EXISTS",
                )
            )
        else:
            target_plan.append(month)

        if target == "gee":
            export_manager.gee_assets_to_save = target_plan
        elif target == "gdrive":
            export_manager.gdrive_assets_to_save = target_plan

    if len(excluded) >= 1:
        message = f"Months already saved in {target.upper()} assets: {excluded}"
        # print(message)
        logger.info(message)

    message = f"Pending months to save in {target.upper()} Assets: {target_plan}"
    # print(message)
    logger.info(message)


def determine_export_plan(export_manager: ExportManager):
    # TODO: Remove redundant code for GEE and GDrive export plans

    logger.debug(f"--- Determining export plan")

    modis_available = export_manager.modis_distinct_months
    planned: list[str] = export_manager.export_plan["planned"]
    excluded = {}
    message = f"Months to save: {planned}"
    # print(message)
    logger.info(message)

    # General Export Plan
    for month in planned:
        if month not in modis_available:
            excluded[month] = "IMAGE_UNAVAILABLE"

    final_plan = [month for month in planned if month not in excluded.keys()]

    export_manager.export_plan["excluded"] = excluded
    export_manager.export_plan["final_plan"] = final_plan

    if len(excluded.keys()) >= 1:
        message = f"Months unavailable or incomplete in MODIS: {list(excluded.keys())}"
        # print(message)
        logger.warning(message)

    # GEE Export Plan
    if export_manager.export_to_gee:
        target_export_plan(
            export_manager=export_manager,
            target="gee",
            export_plan=final_plan,
            existing_imgs=export_manager.gee_saved_assets_months,
            image_prefix=export_manager.image_prefix,
        )

    # Google Drive Export Plan
    if export_manager.export_to_gdrive:
        target_export_plan(
            export_manager=export_manager,
            target="gdrive",
            export_plan=final_plan,
            existing_imgs=export_manager.gdrive_saved_assets_months,
            image_prefix=export_manager.image_prefix,
        )


def calculate_sci_cci(
    ee_MODIS_collection: ImageCollection, all_months_to_save: list
) -> ImageCollection:
    # ## ------ SCI, CCI CALCULATIONS ---------
    logger.debug(f"--- Calculating SCI, CCI")

    try:
        # Calculate SCI, CCI for all images in the collection
        # TODO: create custom function to map over collection with additional arguments
        ee_snow_cloud_collection = ee_MODIS_collection.map(
            calculations.snow_cloud_mask
        ).select("SCI", "CCI")

        # Reduce to monthly images (mean)
        # Only calculating for the months that will be saved.
        ee_monthly_snow_cloud_collection = gee_imagecollection.ic_monthly_mean(
            months=all_months_to_save, imagecollection=ee_snow_cloud_collection
        )

        logger.debug(
            f"Total images in SCI-CCI collection: {ee_monthly_snow_cloud_collection.size().getInfo()}"
        )
        return ee_monthly_snow_cloud_collection

    except Exception as e:
        err_message = "Couldn't calculate SCI, CCI monthly mean."
        logger.exception(err_message)
        raise e


def create_export_tasks_to_gee(
    export_manager: ExportManager,
    ee_monthly_snow_cloud_collection: ImageCollection,
    ee_regions: FeatureCollection,
):

    # TODO: Move scale and other constant to config file
    gee_assets_path = export_manager.gee_assets_path
    image_name = ""
    # Create one export task per image
    for month in export_manager.gee_assets_to_save:
        image_name = f"{export_manager.image_prefix}_{month[:7]}"
        logger.debug(f"Creating export task for GEE: {image_name}")
        try:
            ee_image = ee_monthly_snow_cloud_collection.filterDate(month).first()
            task = batch.Export.image.toAsset(
                **{
                    "image": ee_image,
                    "description": image_name,
                    "assetId": Path(gee_assets_path, image_name).as_posix(),
                    "scale": 500,
                    "region": ee_regions.geometry(),  # type:ignore
                }
            )
            # task = None
            export_manager.export_tasks.add_task(
                exports.ExportTask(
                    image=image_name,
                    date=month,
                    target="gee",
                    status="CREATED",
                    task=task,
                )
            )
        except Exception as e:
            logger.error(f"Export task to GEE for {image_name} failed: {e}")
            export_manager.export_tasks.add_task(
                exports.ExportTask(
                    image=image_name,
                    date=month,
                    target="gee",
                    status="FAILED_TO_CREATE",
                    task=None,
                )
            )
            continue


def create_export_tasks_to_gdrive(
    export_manager: ExportManager,
    ee_monthly_snow_cloud_collection: ImageCollection,
    ee_regions: FeatureCollection,
):

    gdrive_assets_path = Path(export_manager.gdrive_assets_path).as_posix()
    image_name = ""
    for month in export_manager.gdrive_assets_to_save:
        image_name = f"{export_manager.image_prefix}_{month[:7]}"
        logger.debug(f"Preparing to export image to GDrive: {image_name}")
        try:
            ee_image = ee_monthly_snow_cloud_collection.filterDate(month).first()

            task = batch.Export.image.toDrive(
                **{
                    "image": ee_image,
                    "description": image_name,
                    "folder": gdrive_assets_path,
                    "region": ee_regions.geometry(),  # type:ignore
                    "scale": 500,
                    "maxPixels": 1e8,  # Default value is 1e8
                }
            )
            # task = None
            export_manager.export_tasks.add_task(
                exports.ExportTask(
                    image=image_name,
                    date=month,
                    target="gdrive",
                    status="CREATED",
                    task=task,
                )
            )

        except Exception as e:
            logger.error(f"Export task to GDrive for {image_name} failed: {e}")
            export_manager.export_tasks.add_task(
                exports.ExportTask(
                    image=image_name,
                    date=month,
                    target="gdrive",
                    status="FAILED_TO_CREATE",
                    task=None,
                )
            )
            continue


def create_export_tasks(
    export_manager: ExportManager,
    ee_monthly_snow_cloud_collection: ImageCollection,
    ee_regions: FeatureCollection,
) -> None:
    ## ------ EXPORT TASKS ---------
    logger.debug(f"--- Creating Image Export Tasks")

    if export_manager.export_to_gee:
        create_export_tasks_to_gee(
            export_manager=export_manager,
            ee_monthly_snow_cloud_collection=ee_monthly_snow_cloud_collection,
            ee_regions=ee_regions,
        )
    if export_manager.export_to_gdrive:
        create_export_tasks_to_gdrive(
            export_manager=export_manager,
            ee_monthly_snow_cloud_collection=ee_monthly_snow_cloud_collection,
            ee_regions=ee_regions,
        )

    # Start Exports
    start_results = export_manager.export_tasks.start_exports()
    logger.debug(f"Start export results: {start_results}")

    # Track Exports
    track_results = export_manager.export_tasks.track_exports()
    logger.debug(f"Track export results: {track_results}")
