"""
Script to automate the calculation of SCI & CCI monthly average from the images available in the GEE catalog.

SCI: Snow Cover Index
CCI: Cloud Cover Index

This script uses the following conventions:
- Server side variables start with ee_


"""

# libraries
import sys
from typing import Any
import ee
import ee.imagecollection as ee_imagecollection

from snow_ipa.core import workflows
from snow_ipa.core.scripting import init_script_config, error_message
from snow_ipa.core.exporting import ExportManager
from snow_ipa.core.configs import MODIS
from snow_ipa.utils import logs, dates
from snow_ipa.services import connections
from snow_ipa.services.messaging import send_report_message
from snow_ipa.services.gee import (
    imagecollection as gee_imagecollection,
    dates as gee_dates,
)


def main():
    # TODO: Allow user to change image prefix
    script_manager = init_script_config()
    logger = logs.init_logging_config(config=script_manager.config)

    try:
        logger.info("------ STARTING SCRIPT ------")
        script_manager.run_complete_config()
        export_manager = ExportManager(
            export_to_gee=script_manager.export_to_gee,
            export_to_gdrive=script_manager.export_to_gdrive,
            gee_asset_path=script_manager.config["gee_assets_path"],
            gdrive_asset_path=script_manager.config["gdrive_assets_path"],
            months_to_save=script_manager.config["months_list"],
            image_prefix="MOD10A1_SCI_CCI",
        )
    except Exception as e:
        logger.exception(e)
        error_message(e, script_manager)
        raise e

    logger.debug("------ ATTEMPTING CONNECTIONS ------")
    # TODO: Move this to services.connections as a single function
    try:
        runtime_service_account = connections.GoogleServiceAccount(
            script_manager.config["service_credentials_file"]
        )
        connections.connect_to_gee(runtime_service_account)

        if script_manager.export_to_gee:
            connections.check_gee_asset_path(script_manager.config["gee_assets_path"])

        gdrive_service = None
        if script_manager.export_to_gdrive:
            gdrive_service = connections.connect_to_gdrive(runtime_service_account)
            connections.check_gdrive_path(
                asset_path=script_manager.config["gdrive_assets_path"],
                gdrive_service=gdrive_service,
            )

        connections.check_regions(
            asset_path=script_manager.config["regions_asset_path"],
        )

    except Exception as e:
        error_message(e, script_manager)
        raise e

    logger.debug("------ READING MODIS --------")
    """
    Removes images from current month to avoid incomplete months
    and Check if the previous months have all the images expected for that month
    otherwise remove the month as 'incomplete'
    """
    try:
        # Collection path
        modis_status: dict[str, Any] = {"collection": MODIS["path"]}
        ee_MODIS_collection = ee_imagecollection.ImageCollection(MODIS["path"])

        # Total images available
        total_images = ee_MODIS_collection.size().getInfo()  # type: ignore
        modis_status["total_images"] = total_images
        logger.debug(f"Total images in {MODIS['path']}: {total_images}")

        # Last image available
        last_image_dt = ee_MODIS_collection.aggregate_max("system:time_start").getInfo()  # type: ignore
        if not last_image_dt:
            logger.debug("No images available in MODIS collection.")
            raise ValueError("No images available in MODIS collection.")
        last_image_dt = gee_dates.eedate_to_datetime(last_image_dt).strftime("%Y-%m-%d")
        modis_status["last_image"] = last_image_dt
        logger.debug(f"Last image in {MODIS['path']}: {last_image_dt}")

        # Last month available
        ee_MODIS_collection = ee_MODIS_collection.filterDate(
            MODIS["min_month"], dates.current_year_month()
        )

        ee_MODIS_collection = gee_imagecollection.ic_rm_incomplete_months(
            ee_MODIS_collection
        )

        export_manager.modis_distinct_months = (
            gee_imagecollection.ic_get_distinct_months(ee_MODIS_collection)
        )
        try:
            modis_status["last_complete_month"] = export_manager.modis_distinct_months[
                0
            ][:7]
        except IndexError:
            modis_status["last_complete_month"] = ""

        export_manager.modis_status = modis_status

    except Exception as e:
        error_message(e, script_manager)
        raise e

    logger.debug("------ READING ASSETS --------")
    try:
        logger.debug(f"--- Reading Regions")
        ee_regions = ee.featurecollection.FeatureCollection(
            script_manager.config["regions_asset_path"]
        )

        if export_manager.export_to_gee:
            logger.debug(f"--- Reading GEE Assets")
            workflows.get_gee_saved_assets(
                export_manager=export_manager,
                gee_asset_path=script_manager.config["gee_assets_path"],
            )

        if export_manager.export_to_gdrive:
            logger.debug(f"--- Reading GDrive Assets")
            workflows.get_gdrive_saved_assets(
                export_manager=export_manager,
                gdrive_assets_path=script_manager.config["gdrive_assets_path"],
                gdrive_service=gdrive_service,
            )

        workflows.determine_export_plan(export_manager)
        str_export_plan = export_manager.print_export_plan()
        print(str_export_plan)
        logger.info(str_export_plan)

    except Exception as e:
        error_message(e, script_manager)
        raise e

    # TODO: Place below in Try/Except block
    # workflows.determine_export_plan(export_manager)
    if len(export_manager.export_plan["final_plan"]) == 0:
        message = "No new images to save."
        logger.info(message)
        # Print and send results
        if script_manager.email_service:
            logger.debug("------ SENDING REPORT EMAIL --------")
            send_report_message(
                export_manager=export_manager,
                script_start_time=script_manager.start_time,
                email_service=script_manager.email_service,
                from_address=script_manager.config["smtp_from_address"],
                to_address=script_manager.config["smtp_to_address"],
            )
        logger.info("------ FINISHING SCRIPT ------")
        return export_manager

    # Perform SCI and CCI calculations
    ee_monthly_snow_cloud_collection = workflows.calculate_sci_cci(
        ee_MODIS_collection=ee_MODIS_collection,
        all_months_to_save=export_manager.export_plan["final_plan"],
    )

    # Create, start and track Export tasks
    workflows.create_export_tasks(
        export_manager=export_manager,
        ee_monthly_snow_cloud_collection=ee_monthly_snow_cloud_collection,
        ee_regions=ee_regions,
    )

    # Print Export Results
    if export_manager.export_plan["final_plan"]:
        str_export_status = export_manager.print_export_status()

    else:
        str_export_status = "No images to export"

    print("\n")
    print(str_export_status)
    logger.info(str_export_status)

    # Send Export Results
    if script_manager.email_service:
        logger.debug("------ SENDING EMAIL REPORT--------")

        send_report_message(
            export_manager=export_manager,
            script_start_time=script_manager.start_time,
            email_service=script_manager.email_service,
            from_address=script_manager.config["smtp_from_address"],
            to_address=script_manager.config["smtp_to_address"],
        )

    logger.info("------FINISHING SCRIPT ------")
    return export_manager


if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
