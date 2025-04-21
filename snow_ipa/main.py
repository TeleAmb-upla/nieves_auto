"""
Script to automate the calculation of SCI & CCI monthly average from the images available in the GEE catalog.

SCI: Snow Cover Index
CCI: Cloud Cover Index

This script uses the following conventions:
- Server side variables start with ee_


"""

# libraries
import sys
import ee

from snow_ipa.core.scripting import ExportManager, init_script_config, error_message
from snow_ipa.core.configs import DEFAULT_CONFIG, MODIS
from snow_ipa.core import workflows
from snow_ipa.utils import logs, dates
from snow_ipa.services.gee import (
    imagecollection as gee_imagecollection,
)

from snow_ipa.services import connections


def main():
    script_manager = init_script_config()
    logger = logs.init_logging_config(config=script_manager.config)

    logger.info("------ STARTING SCRIPT ------")
    script_manager.run_complete_config()
    try:
        export_manager = ExportManager(
            script_manager.export_to_gee,
            script_manager.export_to_gdrive,
            months_to_save=script_manager.config["months_list"],
            gee_asset_path=script_manager.config["gee_assets_path"],
            gdrive_asset_path=script_manager.config["gdrive_assets_path"],
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

        if script_manager.export_to_gdrive:
            gdrive_service = connections.connect_to_gdrive(runtime_service_account)
            connections.check_gdrive_path(
                asset_path=script_manager.config["gdrive_assets_path"],
                gdrive_service=gdrive_service,
            )
        else:
            gdrive_service = None

        connections.check_regions(
            asset_path=script_manager.config["regions_asset_path"],
        )

    except Exception as e:
        error_message(e, script_manager)
        raise e

    logger.debug("------ READING ASSETS --------")
    try:
        logger.debug(f"--- Reading Regions")
        ee_regions = ee.FeatureCollection(script_manager.config["regions_asset_path"])

        logger.debug(f"--- Reading from MODIS")
        # Removes images from current month to avoid incomplete months
        # and Check if the previous months have all the images expected for that month
        # otherwise remove the month as 'incomplete'

        ee_MODIS_collection = ee.ImageCollection(MODIS["path"])

        ee_MODIS_collection = ee_MODIS_collection.filterDate(
            MODIS["min_month"], dates.current_year_month()
        )
        ee_MODIS_collection = gee_imagecollection.ic_rm_incomplete_months(
            ee_MODIS_collection
        )
        export_manager.modis_distinct_months = (
            gee_imagecollection.ic_get_distinct_months(ee_MODIS_collection)
        )

        workflows.get_gee_saved_assets(
            export_manager=export_manager,
            gee_asset_path=script_manager.config["gee_assets_path"],
        )
        workflows.get_gdrive_saved_assets(
            export_manager=export_manager,
            gdrive_assets_path=script_manager.config["gdrive_assets_path"],
            gdrive_service=gdrive_service,
        )

    except Exception as e:
        error_message(e, script_manager)
        raise e

    # TODO: Place below in Try/Except block
    workflows.determine_export_plan(export_manager)
    # if len(export_manager.export_plan["final_plan"]) == 0:
    #     # TODO: Print Plan
    #     # TODO: Email Plan
    #     message = "No new images to save."
    #     print(message)
    #     logger.info(message)
    #     logger.info("------ EXITING SCRIPT ------")
    #     sys.exit()

    # # Perform SCI and CCI calculations
    # ee_monthly_snow_cloud_collection = workflows.calculate_sci_cci(
    #     ee_MODIS_collection=ee_MODIS_collection,
    #     all_months_to_save=export_manager.export_plan["final_plan"],
    # )

    # # Create, start and track Export tasks
    # workflows.create_export_tasks(
    #     export_manager=export_manager,
    #     ee_monthly_snow_cloud_collection=ee_monthly_snow_cloud_collection,
    #     ee_regions=ee_regions,
    #     gee_path=script_manager.config["gee_asset_path"],
    #     gdrive_path=script_manager.config["google_drive_path"],
    # )
    logger.info("------FINISHING SCRIPT ------")
    return export_manager


if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


# # Send email if enabled
# if email_service:
#     # add export locations to message
#     message = "Exporting images to:"
#     for location in exporting_locations:
#         message += f"\n{location}"

#     # add export status to message
#     message += "\n\nExport Status:"
#     for task in final_task_status:
#         message += f"\n\t{task}"

#     messaging.send_email(
#         server=email_service,
#         message=message,
#         start_time=script_start_time,
#         end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#     )


# # Add a cleanup function to ensure connections are properly closed
# def cleanup_connections(service, email_service):
#     """
#     Cleanup function to close connections to Google Drive and email services.

#     Args:
#         service: Google Drive service instance.
#         email_service: Email service instance.
#     """
#     if service:
#         try:
#             service.close()  # Close Google Drive connection if applicable
#             logger.debug("Google Drive connection closed successfully.")
#         except Exception as e:
#             logger.error("Failed to close Google Drive connection: %s", e)

#     if email_service:
#         try:
#             email_service.quit()  # Close email service connection if applicable
#             logger.debug("Email service connection closed successfully.")
#         except Exception as e:
#             logger.error("Failed to close email service connection: %s", e)


# try:
#     logger.debug(f"----- Script finished successfully")
#     logger.debug(f"------ FINISHING SCRIPT ------")
# except Exception as e:
#     logger.error("An unexpected error occurred: %s", e)
# finally:
#     cleanup_connections(service, email_service)`
