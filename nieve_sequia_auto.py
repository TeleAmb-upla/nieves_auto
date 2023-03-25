"""
Script to automate the calculation of SCI & CCI monthly average from the images available in the GEE cataloge.

SCI: Snow Cover Index
CCI: Cloud Cover Index

This script usess the following conventions:
- Server side variables start with ee_


"""

# libraries
import ee
import geemap
from datetime import datetime, timedelta, date
import json
import pprint
import pathlib
from time import sleep
import os
import sys
import argparse
import logging

# Google API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Custom libraries
from utils.logs import print_log
from utils import dates, dockers, scripting
from gee import dates as gee_dates, assets as gee_assets
from gdrive import assets as drive_assets


# Constants. Used as Defaults in case no alternative is provided.
DEFAULTS = {
    "SERVICE_USER": None,
    "SERVICE_CREDENTIALS_FILE": None,
    "MONTHS_TO_EXPORT": None,
    "REGIONS_ASSET_PATH": "users/proyectosequiateleamb/Regiones/DPA_regiones_nacional",
    "EXPORT_TO": "toAsset",
    "ASSETS_PATH": None,
    "DRIVE_PATH": None,
    "STATUS_CHECK_WAIT": 30,
    "MAX_EXPORTS": 10,
    "MODIS_MIN_MONTH": "2000-03",
}


def rm_incomplete_months_from_ic(
    collection: ee.ImageCollection,
    last_expected_img_dt: datetime = dates.prev_month_last_date(),
) -> ee.ImageCollection:
    """
    Removes last months from an image collection if they don't have all the images for the month. Meaning, it is \'incomplete\'.
    The month is considered incomplete if the image of the last day of the month is not present.

    Args:
        collection: an Image collection
        Last_expected_img_dt: date of the last expected image in a collection.

    Returns: an ImageCollection
    """
    try:
        # Get the date of the last image in the collection
        last_image_dt = ee.Date(
            collection.sort(prop="system:time_start", opt_ascending=False)
            .first()
            .get("system:time_start")
        ).getInfo()
    except Exception as e:
        logging.error("Couldn't get image date from gee")
        raise
    try:
        # Copy date of last image from server
        last_image_dt = gee_dates.format_ee_timestamp(last_image_dt).date()
    except Exception as e:
        logging.error("Couldn't format image date from gee")

    try:
        # Remove the last month if last image != last expected image
        if last_image_dt != last_expected_img_dt:
            incomplete_month = (
                f"{last_expected_img_dt.year}-{last_expected_img_dt.month}"
            )
            msg = f"Removing Incomplete month {incomplete_month} from collection..."
            print(msg)
            logging.info(msg)
            logging.debug(f"\t Last Image Expected: {last_expected_img_dt}")
            logging.debug(f"\t Last Image found: {last_image_dt}")
            new_end_date = last_expected_img_dt.replace(day=1)
            new_end_date_ym = f"{new_end_date.year}-{new_end_date.month}"
            collection = collection.filterDate(
                DEFAULTS["MODIS_MIN_MONTH"], new_end_date_ym
            )
            new_last_month = new_end_date - timedelta(days=1)
            logging.debug(
                f"New last month is: {new_last_month.year}-{new_last_month.month}"
            )
            logging.debug(f"\t New Last Image Expected: {new_last_month}")
            # Recurrent call in case more incomplete months are present
            collection = rm_incomplete_months_from_ic(
                collection=collection, last_expected_img_dt=new_last_month
            )
        else:
            # Return new image collection if there are no incomplete months to remove
            logging.info(
                f"Last complete month in collection: {last_expected_img_dt.year}-{last_expected_img_dt.month}"
            )
        return collection
    except Exception as e:
        logging.error(
            "Couldn't remove images of incomplete months from image collection."
        )
        logging.error(e)
        raise


def get_ic_distinct_months(collection: ee.ImageCollection) -> list:
    """
    Returns a list of distinct months in an image collection.
    Distinct months are represented by the first day of the month.
    For example 2000-01-01 represents January, 2000
    """

    def get_dates(image: ee.Image):
        return ee.Feature(None, {"date": image.date().format("YYYY-MM-dd")})

    ee_dates = collection.map(get_dates).distinct("date").aggregate_array("date")
    collection_dates = ee_dates.getInfo()
    logging.debug(f"Total images in collection: {len(collection_dates)}")

    # Filter dates that are not first day of the month
    distinct_months = []
    for image_date in collection_dates:
        if image_date.endswith("-01"):
            distinct_months.append(image_date)

    distinct_months.sort(reverse=True)
    logging.debug(f"Distinct months in collection: {len(distinct_months)}")
    logging.debug(f"first month: {distinct_months[len(distinct_months)-1]}")
    logging.debug(f"last month: {distinct_months[0]}")

    return distinct_months


def snow_cloud_mask(image:ee.Image) -> ee.Image:
    """
    Calculates SCI and CCI for a given image and returns the image with
    the new SCI, CCI bandas attached.
    Sets NDSI threshold at 40
    Sets Snow_Albedo_Daily_Tile_Class == 150

    """
    NDSI_THRESHOLD = 40
    ee_snow = (
        image.select("NDSI_Snow_Cover").gte(NDSI_THRESHOLD).multiply(100).rename("SCI")
    )
    ee_cloud = (
        image.select("Snow_Albedo_Daily_Tile_Class").eq(150).multiply(100).rename("CCI")
    )

    return image.addBands(ee_snow).addBands(ee_cloud)


def imagecollection_monthly_mean(
    months: list, 
    collection: ee.ImageCollection
) -> ee.ImageCollection:
    """
    Calculates the monthly mean of an ImageCollection

    Arguments:
        months: list of months in format YYYY-MM-DD
        collection: ImageCollection with images from one or more months

    """
    # if months is not a list convert to list
    if type(months) == list:
        pass
    elif type(months) == str:
        # if string check if it's a valid date and convert to list
        # try:
        #     format = "%Y-%m-%d"
        #     res = bool(datetime.strptime(months, format))
        # except ValueError:
        #     res = False
        months = [months]

    ee_image_list = ee.List([])
    for month in months:
        # target month start date
        ee_target_ym = ee.Date(month)
        ee_target_month = ee_target_ym.get("month")
        ee_target_year = ee_target_ym.get("year")
        # target month end date
        ee_post_target_ym = ee_target_ym.advance(1, "month")
        logging.debug(
            f"Processing: {gee_dates.format_ee_timestamp(ee_target_ym.getInfo()).date()} - {gee_dates.format_ee_timestamp(ee_post_target_ym.getInfo()).date()}"
        )

        # Calculate mean
        ee_image = collection.filterDate(ee_target_ym, ee_post_target_ym).mean()
        # Add
        ee_image = ee_image.set("month", ee_target_month)
        ee_image = ee_image.set("year", ee_target_year)
        ee_image = ee_image.set("system:time_start", ee_target_ym.format("YYYY-MM"))

        # add to list of images
        ee_image_list = ee_image_list.add(ee_image)

    # Convert list to image collection
    ee_image_collection = ee.ImageCollection(ee_image_list)
    return ee_image_collection


def get_month_from_asset_name(assets_list: list) -> list:
    # Get list of months from assets names and sort
    # This assums all images found in path end with YYYY-MM
    # TODO: Need to exclude asset or error out if asset_name doesn't end with YYYY-MM
    if assets_list and type(assets_list) is list:
        assets_months = [date[-7:] + "-01" for date in assets_list]
        assets_months.sort(reverse=True)
    else:
        assets_months = []
    return assets_months


def set_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    ## Credential Arguments
    parser.add_argument(
        "-u", "--service-user", dest="user", help="Service account user ID"
    )
    parser.add_argument(
        "-c",
        "--service-credentials",
        dest="credentials",
        help="Service account credentials file location",
    )
    ## Assets Arguments
    parser.add_argument(
        "-s", "--asset-path", dest="asset_path", help="GEE asset path for saving images"
    )
    parser.add_argument(
        "-d",
        "--drive-path",
        dest="drive_path",
        help="Google Drive path for saving images",
    )
    ## Region Arguments
    parser.add_argument(
        "-r",
        "--regions-path",
        dest="regions_path",
        help="GEE asset path for reading regions FeatureCollection",
    )
    ## Output Arguments
    parser.add_argument(
        "-e",
        "--export-to",
        dest="export_to",
        help="Where to export images. Valid options [toAsset | toDrive | toAssetAndDrive]. Default=toAsset ",
        choices=["toAsset", "toDrive", "toAssetAndDrive"],
    )
    ## Time period arguments
    parser.add_argument(
        "-m",
        "--months",
        dest="months",
        help="string of months to export '2022-11-01, 2022-10-01'. Default is to export the last fully available month in MODIS",
    )
    ## logging argumetns
    parser.add_argument(
        "-l",
        "--log-level",
        dest="log_level",
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser


def main() -> None:
    ## ------ PARSE COMMAND LINE ARGUMENTS
    parser = set_argument_parser()
    args = parser.parse_args()

    ## ------ Setup Logging ------------
    ## Read logging from arguments else check Environment var else use default
    # TODO: Move logging setup to separate function
    try:
        if args.log_level:
            log_level = args.log_level.upper()
        else:
            log_level = os.environ["LOG_LEVEL"]
    except:
        log_level = "INFO"

    ## If incorrect log level was provided, default to "INFO"
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "EXCEPTION"):
        log_level = "INFO"

    ## Get numerical value of log level.
    num_log_level = getattr(logging, log_level, None)

    ## Set log file for log output.
    # TODO: Give user an option to change log file
    log_file = "snow.log"

    ## Configure logging
    logging.basicConfig(
        filename=log_file,
        encoding="utf-8",
        level=num_log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info("------ STARTING SCRIPT ------")

    ## ------ SCRIPT SETUP ---------
    logging.debug("---Initiating script setup")
    # Set script config from environmental vars
    try:
        SERVICE_USER = scripting.set_script_config_var(
            var="SERVICE_USER",
            arg_value=args.user,
            default=DEFAULTS["SERVICE_USER"],
            required=True,
        )
        SERVICE_CREDENTIALS_FILE = scripting.set_script_config_var(
            var="SERVICE_CREDENTIALS_FILE",
            arg_value=args.credentials,
            default=DEFAULTS["SERVICE_CREDENTIALS_FILE"],
            required=True,
        )
        REGIONS_ASSET_PATH = scripting.set_script_config_var(
            var="REGIONS_ASSET_PATH",
            arg_value=args.regions_path,
            default=DEFAULTS["REGIONS_ASSET_PATH"],
            required=True,
        )
        EXPORT_TO = scripting.set_script_config_var(
            var="EXPORT_TO",
            arg_value=args.export_to,
            default=DEFAULTS["EXPORT_TO"],
            required=True,
        )
        # if EXPORT_TO == "toAsset":
        ASSETS_PATH = scripting.set_script_config_var(
            var="ASSETS_PATH",
            arg_value=args.asset_path,
            default=DEFAULTS["ASSETS_PATH"],
            required=(EXPORT_TO in ["toAsset", "toAssetAndDrive"]),
        )
        # if EXPORT_TO == "toDrive":
        DRIVE_PATH = scripting.set_script_config_var(
            var="DRIVE_PATH",
            arg_value=args.drive_path,
            default=DEFAULTS["DRIVE_PATH"],
            required=(EXPORT_TO in ["toDrive", "toAssetAndDrive"]),
        )
        MONTHS_TO_EXPORT = scripting.set_script_config_var(
            var="MONTHS_TO_EXPORT",
            arg_value=args.months,
            default=DEFAULTS["MONTHS_TO_EXPORT"],
            parse="List",
        )
    except Exception as err:
        print_log(err.args[0], "ERROR")
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    # Exit if credentials file doesn't exist
    # Search for file in given path and docker secrets
    try:
        if SERVICE_CREDENTIALS_FILE and type(SERVICE_CREDENTIALS_FILE) is str:
            SERVICE_CREDENTIALS_FILE = dockers.check_docker_secret(SERVICE_CREDENTIALS_FILE)
        else:
            raise Exception('Incorrect vartype or value is missing')
    except Exception as e:
        print_log(f"SERVICE_CREDENTIALS_FILE - {e}", "ERROR")
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    # Exit if MONTHS_TO_EXPORT variable was provided but has incorrect values
    if MONTHS_TO_EXPORT:
        if not dates.check_valid_date_list(MONTHS_TO_EXPORT):
            print_log(
                "One or more dates provided in MONTHS_TO_EXPORT are not valid", "ERROR"
            )
            logging.info("------ EXITING SCRIPT ------")
            sys.exit()

    ## ------ GEE CONNECTION ---------
    logging.debug("--- Connecting to GEE")
    # Connect to GEE using service account for automation
    try:
        credentials = ee.ServiceAccountCredentials(
            SERVICE_USER, SERVICE_CREDENTIALS_FILE
        )
        ee.Initialize(credentials) #type:ignore
        logging.debug("GEE connection successful")
    except Exception as err:
        print_log(err.args[0], "ERROR")
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    ## ------ GOOGLE DRIVE CONNECTION --------
    if EXPORT_TO in ["toDrive", "toAssetAndDrive"]:
        logging.debug("--- Connecting to Google Drive")
        try:
            # Connect to Google API and build service
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_CREDENTIALS_FILE
            )
            service = build("drive", "v3", credentials=creds)
        except HttpError as error:
            print_log(error.args[0], "ERROR")
            logging.info("------ EXITING SCRIPT ------")
            sys.exit()
    else:
        service=None
    ## ------ CHECK GEE ASSET PATH OR GOOGLE DRIVE PATH ARE VALID --------
    # GEE Assets
    if EXPORT_TO in ["toAsset", "toAssetAndDrive"]:
        try:
            if not gee_assets.check_folder_exists(path=ASSETS_PATH):
                raise Exception(f"GEE Asset folder not found: {ASSETS_PATH}")
        except Exception as error:
            print_log(error.args[0], "ERROR")
            logging.info("------ EXITING SCRIPT ------")
            sys.exit()

    # Google Drive
    if EXPORT_TO in ["toDrive", "toAssetAndDrive"]:
        try:
            if not drive_assets.check_folder_exists(
                drive_service=service, 
                path=DRIVE_PATH #type:ignore
            ):
                raise Exception(f"Google Drive folder not found: {DRIVE_PATH}")
        except Exception as error:
            print_log(error.args[0], "ERROR")
            logging.info("------ EXITING SCRIPT ------")
            sys.exit()

    ## ------ READING REGIONS ---------
    logging.debug("--- Reading regions")
    # Check if "DPA_regiones_nacionales" feature collection exists else stop script
    # NOTE: This is very specific to this project and might not translate to other uses.
    try:
        if gee_assets.check_asset_exists(REGIONS_ASSET_PATH, "TABLE"): #type:ignore
            ee_territorio_nacional = ee.FeatureCollection(REGIONS_ASSET_PATH)

    except:
        print_log("Could not read Regions. Terminating Script", "ERROR")
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    ## ------ READING FROM MODIS ---------
    logging.debug(f"--- Reading from MODIS")
    # Get MODIS image Collection.
    # Removes images from current month to avoid incomplete months
    # and Check if the previous months have all the images expected for that month
    # otherwise remove the month as 'incomplete'
    try:
        ee_MODIS_collection = ee.ImageCollection("MODIS/006/MOD10A1")
    except Exception as e:
        print_log("Couldn't read from MODIS. Terminating Script", "ERROR")
        logging.error(e)
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    try:
        ee_MODIS_collection = ee_MODIS_collection.filterDate(
            DEFAULTS["MODIS_MIN_MONTH"], dates.current_year_month()
        )
        ee_MODIS_collection = rm_incomplete_months_from_ic(ee_MODIS_collection)
        MODIS_distinct_months = get_ic_distinct_months(ee_MODIS_collection)

    except Exception as e:
        print_log(
            "Couldn't remove incomplete months from MODIS collection. Terminating Script",
            "ERROR",
        )
        logging.error(e)
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    ## ------ CHECKING IMAGES ALREADY SAVED ---------
    logging.debug(f"--- Checking for images already saved")
    # Get list of images already saved in given path.

    # GEE Assets
    gee_saved_assets=[]
    gee_saved_assets_months=[]
    try:
        if EXPORT_TO in ["toAsset", "toAssetAndDrive"]:
            if ASSETS_PATH and type(ASSETS_PATH) is str:
                gee_saved_assets = gee_assets.get_asset_list(ASSETS_PATH, "IMAGE")
            gee_saved_assets_months = get_month_from_asset_name(gee_saved_assets)
            logging.debug(
                f"Total images saved in GEE Asset folder: {len(gee_saved_assets_months)}"
            )
            if len(gee_saved_assets_months) > 0:
                logging.debug(f"first month saved: {gee_saved_assets_months[-1]}")
                logging.debug(f"last month saved: {gee_saved_assets_months[0]}")
    except Exception as e:
        print_log("Couldn't list images already saved to GEE Assets.", "ERROR")
        logging.error(e)
        logging.info("------ EXITING SCRIPT ------")

    # Goolge Drive
    gdrive_saved_assets=[]
    gdrive_saved_assets_months=[]
    try:
        if EXPORT_TO in ["toDrive", "toAssetAndDrive"]:
            gdrive_saved_assets = drive_assets.get_asset_list(
                drive_service=service, path=DRIVE_PATH, asset_type="IMAGE"
            )
            if type(gdrive_saved_assets) is list:
                gdrive_saved_assets_months = get_month_from_asset_name(gdrive_saved_assets)
            else:
                gdrive_saved_assets_months=[]
            msg = "Total images saved in Google Drive folder"
            logging.debug(f"{msg}: {len(gdrive_saved_assets_months)}")
            if len(gdrive_saved_assets_months) > 0:
                logging.debug(f"first month saved: {gdrive_saved_assets_months[-1]}")
                logging.debug(f"last month saved: {gdrive_saved_assets_months[0]}")
    except Exception as e:
        print_log("Couldn't list images already saved to Google Drive", "ERROR")
        logging.error(e)
        logging.info("------ EXITING SCRIPT ------")

    ## ------ DETERMINE MONTHS TO SAVE ---------
    logging.debug(f"--- Determining dates to save")
    # Save images requested through MONTHS_TO_EXPORT otherwise save
    # the last available month in MODIS

    if MONTHS_TO_EXPORT:
        months_to_save = MONTHS_TO_EXPORT

    else:
        try:
            # Get last complete available month from MODIS
            last_available = MODIS_distinct_months[0]
            months_to_save = [last_available]
        except:
            months_to_save = []
    print_log(f"Months to save: {months_to_save}", "INFO")

    # Identify months that are not available
    months_not_available = [
        month for month in months_to_save if month not in MODIS_distinct_months
    ]
    if len(months_not_available) >= 1:
        print_log(
            f"Months not available or complete in MODIS: {months_not_available}",
            "WARNING",
        )

    # Check if months to save have already been saved or are not available/complete in MODIS
    # GEE Assets
    gee_months_to_save = []
    if EXPORT_TO in ["toAsset", "toAssetAndDrive"]:
        gee_months_already_saved = [
            month for month in months_to_save if month in gee_saved_assets_months
        ]
        gee_months_to_save = [
            month
            for month in months_to_save
            if (
                month not in gee_months_already_saved
                and month not in months_not_available
            )
        ]
        if len(gee_months_already_saved) >= 1:
            print_log(
                f"Months already saved in GEE Assets: {gee_months_already_saved}",
                "WARNING",
            )
        print_log(f"Pending months to save in GEE Assets: {gee_months_to_save}", "INFO")

    # Google Drive
    gdrive_months_to_save = []
    if EXPORT_TO in ["toDrive", "toAssetAndDrive"]:
        gdrive_months_already_saved = [
            month for month in months_to_save if month in gdrive_saved_assets_months
        ]
        gdrive_months_to_save = [
            month
            for month in months_to_save
            if (
                month not in gdrive_months_already_saved
                and month not in months_not_available
            )
        ]
        if len(gdrive_months_already_saved) >= 1:
            print_log(
                f"Months already saved in Google Drive: {gdrive_months_already_saved}",
                "WARNING",
            )
        print_log(
            f"Pending months to save in Google Drive: {gdrive_months_to_save}", "INFO"
        )

    # Stop script if there's nothing new to export
    all_months_to_save = list(set(gee_months_to_save + gdrive_months_to_save))
    all_months_to_save.sort()
    if len(all_months_to_save) == 0:
        print_log(f"No new months to save. Exiting script", "INFO")
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    ## ------ SCI, CCI CALCULATIONS ---------
    logging.debug(f"--- Calculationg SCI, CCI")
    ## ONLY RUNS IF MONTHS TO SAVE >= 1

    try:
        # Calculate and select snow and cloud bands
        ee_snow_cloud_collection = ee_MODIS_collection.map(snow_cloud_mask).select(
            "SCI", "CCI"
        )

        # Calculate mean per month
        # Only calculating it for the months that will be saved.
        ee_monthly_snow_cloud_collection = imagecollection_monthly_mean(
            all_months_to_save, ee_snow_cloud_collection
        )

    except Exception as e:
        print_log(
            "Couldn't calculate SCI, CCI monthly mean. Terminating Script", "ERROR"
        )
        print_log(e.args[0], "ERROR")
        logging.info("------ EXITING SCRIPT ------")
        sys.exit()

    ## ------ EXPORT TASKS ---------
    logging.debug(f"--- Exporting Images")

    msg = print_log("Exporting targets:", "INFO")
    if EXPORT_TO in ["toAsset", "toAssetAndDrive"]:
        print_log(f"\t -GEE Assets: {ASSETS_PATH}", "INFO")

    if EXPORT_TO in ["toDrive", "toAssetAndDrive"]:
        print_log(f"\t -Google Drive: {DRIVE_PATH}", "INFO")

    print_log(f"Exports:", "INFO")
    # Setting a maximum number of images to export in a single run.
    # limiting in case something goes wrong.
    max_exports = DEFAULTS["MAX_EXPORTS"]
    export_tasks = []
    # Start one export task per image per export target (gee, drive)
    for month in all_months_to_save:
        # Exit if max number of exports is reached
        if max_exports == 0:
            print_log(
                f'Reached limit of {DEFAULTS["MAX_EXPORTS"]} maximum exports in one run. You can increase this limit through the MAX_EXPORTS environment variable or argument',
                "WARNING",
            )
            break
        else:
            max_exports -= 1
        try:
            ee_image = ee_monthly_snow_cloud_collection.filterDate(month).first()
            image_ym = ee_image.get("system:time_start").getInfo()
            image_name = "MOD10A1_SCI_CCI_" + image_ym

            # GEE Assets
            if (
                EXPORT_TO in ["toAsset", "toAssetAndDrive"]
                and month in gee_months_to_save
            ):
                print_log(f"-Exporting image to GEE Asset: {image_name}", "INFO")
                task = ee.batch.Export.image.toAsset(
                    **{
                        "image": ee_image,
                        "description": image_name,
                        "assetId": pathlib.Path(ASSETS_PATH, image_name).as_posix(), #type:ignore
                        "scale": 500,
                        "region": ee_territorio_nacional.geometry(), #type:ignore
                    }
                )
                export_tasks.append(
                    {"task": task, "target": "GEE Asset", "image": image_name}
                )

            # Google Drive
            if (
                EXPORT_TO in ["toDrive", "toAssetAndDrive"]
                and month in gdrive_months_to_save
            ):
                print_log(f"-Exporting image to Google Drive: {image_name}", "INFO")
                # NOTE: Be aware, if there are multiple folders with he same name
                # this function might not export to the correct one!!!
                task = ee.batch.Export.image.toDrive(
                    **{
                        "image": ee_image,
                        "description": image_name,
                        "scale": 500,
                        "region": ee_territorio_nacional.geometry(), #type:ignore
                        "maxPixels": 1e8,
                        "folder": pathlib.Path(DRIVE_PATH).as_posix(), #type:ignore
                    }
                )
                export_tasks.append(
                    {"task": task, "target": "Google Drive", "image": image_name}
                )
        except Exception as e:
            print_log(
                f"couldn't create 1 or more export task for image: {image_name}",
                "ERROR",
            )
            logging.error(e)

    # Start tasks
    for task in export_tasks:
        try:
            task["task"].start()
        except Exception as e:
            msg = f"Export Task failed for {task['target']} {task['image']}: {task['task']}"
            print_log(msg, "ERROR")
            logging.error(e)

    print_log("--- Checking Export Status...", "INFO")
    # Check exports until all are complete or fail
    export_running = True
    tasks_finished = []
    while export_running:
        # Assume all finished unless told otherwise
        export_running = False
        for i, task in enumerate(export_tasks):
            if i not in tasks_finished:
                status = task["task"].status()
                msg = f"{task['image']} to {task['target']}: {status['state']}"
                if status["state"] in ("UNSUBMITTED"):
                    print_log(msg, "INFO")
                    # print_log(f"{status['description']}: {status['state']}", "INFO")
                    tasks_finished.append(i)
                elif status["state"] in ("SUBMITTED", "READY", "RUNNING"):
                    # keep loop running if there's at least one unfinished task
                    export_running = True
                elif status["state"] in ("COMPLETED", "CANCEL_REQUESTED", "CANCELLED"):
                    print_log(msg, "INFO")
                    # print_log(f"{status['description']}: {status['state']}", "INFO")
                    tasks_finished.append(i)
                elif status["state"] in ("FAILED"):
                    print_log(msg, "INFO")
                    # print_log(f"{status['description']}: {status['state']}", "INFO")
                    print_log(f"{status['error_message']}", "ERROR")
                    tasks_finished.append(i)
        if export_running:
            sleep(DEFAULTS["STATUS_CHECK_WAIT"])

    logging.debug(f"----- Script finnished successfully")
    logging.debug(f"------ FINISHING SCRIPT ------")


if __name__ == "__main__":
    main()
