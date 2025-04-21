import logging

# import ee
# from pathlib import Path

from snow_ipa.core.scripting import ExportManager

from snow_ipa.services.gee import (
    assets as gee_assets,
    exports,
)  # , calculations, exports

# from snow_ipa.services.gee import imagecollection as gee_imagecollection
from snow_ipa.services.gdrive import assets as gdrive_assets

logger = logging.getLogger(__name__)

# TODO: Replace constants with config values
# TODO: Set max number of exports


# GEE Assets
def get_gee_saved_assets(export_manager: ExportManager, gee_asset_path: str):
    """
    Get the list of saved assets in Google Earth Engine (GEE).

    Args:
        export_manager (ExportManager): The export manager instance.
        gee_asset_path (str): The path to the GEE assets.

    Returns:
        list: List of saved assets in GEE.
    """
    logger.debug(f"--- Checking for images already saved to GEE")
    try:

        gee_saved_assets = gee_assets.get_asset_list(gee_asset_path, "IMAGE")
        gee_saved_assets_months = gee_assets.get_trailing_ymd(gee_saved_assets)
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
        gdrive_saved_assets_months = gee_assets.get_trailing_ymd(gdrive_saved_assets)
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


def determine_export_plan(export_manager: ExportManager):
    # TODO: Fix export date comparison, some dates are in YYYY-MM-DD and others in YYYY-MM format
    # NOTE: Planned is in YYYY-MM format
    # NOTE: MODIS is in YYYY-MM-DD format
    # NOTE: GEE and GDrive are in YYYY-MM-DD format

    logger.debug(f"--- Determining export plan")

    modis_available = export_manager.modis_distinct_months
    planned = export_manager.export_plan["planned"]
    excluded = {}
    message = f"Months to save: {planned}"
    print(message)
    logger.info(message)

    # Export Plan

    for month in planned:
        if month in modis_available:
            excluded[month] = "IMAGE_UNAVAILABLE"

    final_plan = [month for month in planned if month not in excluded.keys()]

    export_manager.export_plan["excluded"] = excluded
    export_manager.export_plan["final_plan"] = final_plan

    if len([excluded.keys()]) >= 1:
        message = f"Months unavailable or incomplete in MODIS: {[excluded.keys()]}"
        print(message)
        logger.warning(message)

    # GEE Export Plan
    if export_manager.export_to_gee:
        gee_planned = []
        gee_excluded = {}
        for month in final_plan:
            image_name = f"{export_manager.image_prefix}_{month}"
            if month in export_manager.gee_saved_assets_months:
                gee_excluded[month] = "ALREADY_EXISTS"
                export_manager.export_tasks.add_task(
                    exports.ExportTask(
                        image=image_name,
                        date=month,
                        target="gee",
                        status="ALREADY_EXISTS",
                    )
                )
            else:
                gee_planned.append(month)

        if len(gee_excluded.keys()) >= 1:
            message = f"Months already saved in GEE Assets: {[gee_excluded.keys()]}"
            print(message)
            logger.info(message)

        message = f"Pending months to save in GEE Assets: {gee_planned}"
        print(message)
        logger.info(message)

    # Google Drive Export Plan
    if export_manager.export_to_gdrive:
        gdrive_planned = []
        gdrive_excluded = {}
        for month in final_plan:
            image_name = f"{export_manager.image_prefix}_{month}"
            if month in export_manager.gdrive_saved_assets_months:
                gdrive_excluded[month] = "ALREADY_EXISTS"
                export_manager.export_tasks.add_task(
                    exports.ExportTask(
                        image=image_name,
                        date=month,
                        target="gdrive",
                        status="ALREADY_EXISTS",
                    )
                )
            else:
                gdrive_planned.append(month)

        if len(gee_excluded.keys()) >= 1:
            message = (
                f"Months already saved in GDRIVE Assets: {[gdrive_excluded.keys()]}"
            )
            print(message)
            logger.info(message)

        message = f"Pending months to save in GDRIVE Assets: {gdrive_planned}"
        print(message)
        logger.info(message)

    export_manager.gee_assets_to_save = gee_planned
    export_manager.gdrive_assets_to_save = gdrive_planned


# def calculate_sci_cci(
#     ee_MODIS_collection: ee.ImageCollection, all_months_to_save: list
# ) -> ee.ImageCollection:
#     # ## ------ SCI, CCI CALCULATIONS ---------
#     logger.debug(f"--- Calculating SCI, CCI")

#     try:
#         # Calculate SCI, CCI for all images in the collection
#         # TODO: create custom function to map over collection with additional arguments
#         ee_snow_cloud_collection = ee_MODIS_collection.map(
#             calculations.snow_cloud_mask
#         ).select("SCI", "CCI")

#         # Reduce to monthly images (mean)
#         # Only calculating it for the months that will be saved.
#         ee_monthly_snow_cloud_collection = gee_imagecollection.ic_monthly_mean(
#             months=all_months_to_save, imagecollection=ee_snow_cloud_collection
#         )

#         return ee_monthly_snow_cloud_collection

#     except Exception as e:
#         err_message = "Couldn't calculate SCI, CCI monthly mean. Terminating Script"
#         logger.error(err_message, exc_info=True)
#         raise e


# def create_export_tasks_to_gee(
#     export_manager: ExportManager,
#     ee_monthly_snow_cloud_collection: ee.ImageCollection,
#     gee_path: str,
#     ee_regions: ee.FeatureCollection,
# ):

#     # TODO: Move Name Prefix, scale and other constant to config file
#     image_name = ""
#     # Start one export task per image per export target (gee, drive)
#     for month in export_manager.gee_assets_to_save:
#         image_name = f"{export_manager.image_prefix}_{month}"
#         logger.debug(f"Preparing to export image to GEE: {image_name}")
#         try:
#             ee_image = ee_monthly_snow_cloud_collection.filterDate(month).first()
#             task = ee.batch.Export.image.toAsset(
#                 **{
#                     "image": ee_image,
#                     "description": image_name,
#                     "assetId": Path(gee_path, image_name).as_posix(),
#                     "scale": 500,
#                     "region": ee_regions.geometry(),  # type:ignore
#                 }
#             )
#             export_manager.export_tasks.add_task(
#                 exports.ExportTask(
#                     image=image_name,
#                     date=month,
#                     target="gee",
#                     status="CREATED",
#                     task=task,
#                 )
#             )
#         except Exception as e:
#             logger.error(f"Export task to GEE for {image_name} failed: {e}")
#             export_manager.export_tasks.add_task(
#                 exports.ExportTask(
#                     image=image_name,
#                     date=month,
#                     target="gee",
#                     status="FAILED_TO_CREATE",
#                     task=None,
#                 )
#             )
#             continue


# def create_export_tasks_to_gdrive(
#     export_manager: ExportManager,
#     ee_monthly_snow_cloud_collection: ee.ImageCollection,
#     gdrive_path: str,
#     ee_regions: ee.FeatureCollection,
# ):

#     for month in export_manager.gdrive_assets_to_save:
#         image_name = f"{export_manager.image_prefix}_{month}"
#         logger.debug(f"Preparing to export image to GDrive: {image_name}")
#         try:
#             ee_image = ee_monthly_snow_cloud_collection.filterDate(month).first()

#             task = ee.batch.Export.image.toDrive(
#                 **{
#                     "image": ee_image,
#                     "description": image_name,
#                     "scale": 500,
#                     "region": ee_regions.geometry(),  # type:ignore
#                     "maxPixels": 1e8,  # Default value is 1e8
#                     "folder": Path(gdrive_path).as_posix(),
#                 }
#             )
#             export_manager.export_tasks.add_task(
#                 exports.ExportTask(
#                     image=image_name,
#                     date=month,
#                     target="gdrive",
#                     status="CREATED",
#                     task=task,
#                 )
#             )

#         except Exception as e:
#             logger.error(f"Export task to GDrive for {image_name} failed: {e}")
#             export_manager.export_tasks.add_task(
#                 exports.ExportTask(
#                     image=image_name,
#                     date=month,
#                     target="gdrive",
#                     status="FAILED_TO_CREATE",
#                     task=None,
#                 )
#             )
#             continue


# def create_export_tasks(
#     export_manager: ExportManager,
#     ee_monthly_snow_cloud_collection: ee.ImageCollection,
#     ee_regions: ee.FeatureCollection,
#     gee_path: str,
#     gdrive_path: str,
# ) -> None:
#     ## ------ EXPORT TASKS ---------
#     logger.debug(f"--- Creating Image Export Tasks")
#     create_export_tasks_to_gee(
#         export_manager=export_manager,
#         ee_monthly_snow_cloud_collection=ee_monthly_snow_cloud_collection,
#         gee_path=gee_path,
#         ee_regions=ee_regions,
#     )
#     create_export_tasks_to_gdrive(
#         export_manager=export_manager,
#         ee_monthly_snow_cloud_collection=ee_monthly_snow_cloud_collection,
#         gdrive_path=gdrive_path,
#         ee_regions=ee_regions,
#     )

#     # Start Exporting and tracking
#     export_results = export_manager.export_tasks.track_exports(sleep_time=60)
