'''
Script to automate the calculation of SCI & CCI monthly average from the images available in the GEE cataloge.

SCI: Snow Cover Index
CCI: Cloud Cover Index

This script usess the following conventions:
- Server side variables start with ee_


'''

# libraries
import ee
import geemap
from datetime import datetime, timedelta
import pytz
import json
import pprint
import pathlib
from math import ceil
from time import sleep
from yaspin import yaspin
import os
import sys
import argparse

# Constants
SNOW_SERVICE_USER = None
SNOW_SERVICE_CREDENTIALS_FILE = None
SNOW_MONTHS_TO_EXPORT = None
SNOW_REGIONS_ASSET_PATH = 'users/proyectosequiateleamb/Regiones/DPA_regiones_nacional'
SNOW_EXPORT_TO = 'toAsset'
SNOW_ASSETS_PATH = 'projects/ee-proyectosequiateleamb/assets/nieve/raster_sci_cci'
SNOW_DRIVE_PATH = None
SNOW_STATUS_CHECK_WAIT = 30
SNOW_MAX_EXPORTS = 10
GEE_PATHPREFIX = 'projects/earthengine-legacy/assets/'
MODIS_MIN_MONTH = '2000-03'
UTC_TZ=pytz.timezone('UTC')

def check_docker_secret(var):
    '''
    Checks if file exists in given path or in docker secrets. 
    Returns None if file is not found or the file path if exits. 
    '''
    docker_secrets_path = "/var/run/secrets"
    var_path=pathlib.Path(var)
    docker_var_path = pathlib.Path(docker_secrets_path,var)   

    if len(var_path.parts) > 1 and var_path.exists():
            return var_path.as_posix()

    elif docker_var_path.exists():
            return docker_var_path.as_posix()
    else:
        print(f"file not found {var}")
        return None
        
def set_script_config_var (var, required=False, parse=None):
    try: 
        # Check the required variable exists 
        assert var in globals()
    except:
        print(f"Unknown variable")
        sys.exit(0)
    try:
        value =  os.environ[var]
        if parse == 'List':
            value = [item.strip() for item in value.split(",")]
        print(f"{var}: {value}")
    except KeyError:
        value = globals()[var]
        print(f'Using default value: {var}={value}')
    
    if required==True and value==None:
        print(f"{var} is required but no value was set")
        sys.exit(0)
    else:
        return value

def current_year_month()->str:
    '''
    Returns the current year and month from local machine time as a string
    e.g. 2022-12
    '''
    return str(datetime.today().year) + "-" + str(datetime.today().month)

def prev_month_last_date():
    '''
    Returns the last day of the previous month relative to the current date 
    Current date is taken from datetime.today()
    Returns a date object
    '''
    return datetime.today().date().replace(day=1) - timedelta(days=1)

def format_ee_timestamp(dt, tz=UTC_TZ):
    '''
    Formats a date retreived from GEE using a given timezon. 
    Default timezone is UTC
    '''
    return datetime.fromtimestamp(dt['value']/1000, tz)

def print_ee_timestamp(dt, tz=UTC_TZ):
    '''
    Prints a date retreived from gee using a given Timezone. 
    Default timezone is UTC
    '''
    print(format_ee_timestamp(dt, tz))

def get_asset_list(parent, asset_type=None):
    '''List assets from an assets foler in GGE

    reference: https://github.com/spatialthoughts/projects/blob/master/ee-python/list_all_assets.py
    '''
    try:
        parent_asset = ee.data.getAsset(parent)
    except:
        print(f"Can't find asset: {parent}")
        raise
    parent_id = parent_asset['name']
    parent_type = parent_asset['type']
    asset_list = []
    try:
        child_assets = ee.data.listAssets({'parent': parent_id})['assets']
    except:    
        print(f"Can't list objects in: {parent}")
        raise
    for child_asset in child_assets:
        child_id = child_asset['name']
        child_type = child_asset['type']
        # print(f"{child_id}:{child_type}")
        if child_type in ['FOLDER','IMAGE_COLLECTION']:
            # Recursively call the function to get child assets
            asset_list.extend(get_asset_list(child_id))
        else:
            if type(asset_type) == str:
                asset_type=[asset_type]
            if child_type in asset_type or child_type == None:
                asset_list.append(child_id)
    return asset_list

def check_asset_exists(asset: str, asset_type=None):
    '''Test if feature collection is in the asset list.
    Returns True if asset is found, False if it isn't
    '''

    asset_path = pathlib.Path(asset).parent.as_posix()
    print(f"Searching for: {asset}")

    # Get list of assets in given path
    try: 
        asset_list = get_asset_list(asset_path, asset_type=asset_type)
        # Print list of assets found
        print('Found {} assets'.format(len(asset_list)))
        # for asset_x in asset_list:
        #    print(asset_x)

    except:
        print("Asset list could not be retreived")

    # Check if asset is in asset list
    asset_found = False
    for asset_x in asset_list:
        if GEE_PATHPREFIX + asset == asset_x:
            asset_found = True

    print(f"Asset successfully found: {asset_found}")
    return asset_found

def rm_incomplete_months_from_ic(collection, last_expected_img_dt=prev_month_last_date()):
    '''
    Remove last month from an image collection if it doesn't have all the images for the month
    The month is removed if the image of the last day of the month is not present.
    Returns: an ImageCollection
    '''
# TODO: MAke this a reursive function to eliminate last months until we find a full month
    last_image_dt = ee.Date(collection.sort(
        prop='system:time_start', 
        opt_ascending=False
        ).first().get('system:time_start')).getInfo()

    last_image_dt = format_ee_timestamp(last_image_dt).date()

    if last_image_dt!=last_expected_img_dt:
        print("Images from the previous month might be missing:")
        print(f"\t Last Image Expected: {last_expected_img_dt}")
        print(f"\t Last Image found: {last_image_dt}")
        incomplete_month = f"{last_expected_img_dt.year}-{last_expected_img_dt.month}"
        print(f"Removing Incomplete month {incomplete_month} from collection...")
        new_end_date = last_expected_img_dt.replace(day=1)
        new_end_date_ym = f"{new_end_date.year}-{new_end_date.month}"
        collection = collection.filterDate(MODIS_MIN_MONTH, new_end_date_ym)
        new_last_month = new_end_date - timedelta(days=1)
        print(f"New last month is: {new_last_month.year}-{new_last_month.month}")

    else:
        print(f"Last complete month: {last_expected_img_dt.year}-{last_expected_img_dt.month}")
    return collection

def get_ic_distinct_months(collection):
    '''
    Returns a list of distinct months in an image collection. 
    Distinct months are represented by the first day of the month. 
    For example 2000-01-01 represents January, 2000
    '''
    def get_dates(image):
        return ee.Feature(None, {'date': image.date().format('YYYY-MM-dd')})

    ee_dates = collection.map(get_dates).distinct('date').aggregate_array('date')
    collection_dates = ee_dates.getInfo()
    print(f"Total images in collection: {len(collection_dates)}")
    # Filter dates that are not first day of the month
    distinct_months = []
    for image_date in collection_dates:
        if image_date.endswith('-01'):
            distinct_months.append(image_date)

    distinct_months.sort(reverse=True)
    print(f"Distinct months in collection: {len(distinct_months)}")
    print(f"first month: {distinct_months[len(distinct_months)-1]}")
    print(f"last month: {distinct_months[0]}")

    return distinct_months

def snow_cloud_mask(image): 
    '''
    Calculates SCI and CCI for a given image and returns the image with
    the new SCI, CCI bandas attached.
    Sets NDSI threshold at 40
    Sets Snow_Albedo_Daily_Tile_Class == 150

    '''
    NDSI_THRESHOLD = 40
    ee_snow = image.select('NDSI_Snow_Cover').gte(NDSI_THRESHOLD).multiply(100).rename('SCI')
    ee_cloud = image.select('Snow_Albedo_Daily_Tile_Class').eq(150).multiply(100).rename('CCI')
    
    return image.addBands(ee_snow).addBands(ee_cloud)

def imagecollection_monthly_mean(months: list, collection):
    '''
    Calculates the monthly mean of an ImageCollection
    
    Arguments:
        months: list of months in format YYYY-MM-DD
        collection: ImageCollection with images from one or more months

    '''
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
        ee_target_ym=ee.Date(month)
        ee_target_month=ee_target_ym.get('month')
        ee_target_year=ee_target_ym.get('year')
        # target month end date
        ee_post_target_ym=ee_target_ym.advance(1,"month")
        print(f"Processing: {format_ee_timestamp(ee_target_ym.getInfo()).date()} - {format_ee_timestamp(ee_post_target_ym.getInfo()).date()}")

        # Calculate mean
        ee_image = collection.filterDate(ee_target_ym, ee_post_target_ym).mean()
        # Add 
        ee_image = ee_image.set('month', ee_target_month)
        ee_image = ee_image.set('year', ee_target_year)
        ee_image = ee_image.set('system:time_start', ee_target_ym.format('YYYY-MM'))

        # add to list of images
        ee_image_list=ee_image_list.add(ee_image)
    
    # Convert list to image collection
    ee_image_collection = ee.ImageCollection(ee_image_list)
    return ee_image_collection

def check_gee_task_status(task, wait_time=0, spinner=True):
    sleep_time = 30
    if wait_time == 0:
        # run for max 24 hours"
        max_runs = ceil((24*60*60)/sleep_time)
    else:
        max_runs = ceil(wait_time/sleep_time)
    
    check_status=True
    runs = 0
    if spinner:
        spinner = yaspin()
        spinner.start()
    while check_status:
        task_status = task.status()
        if spinner:
            spinner.text=f"status: {task_status['state']}"
        # print(task_status['state'])
        if task_status['state'] in ('READY','RUNNING'):
            sleep(sleep_time)
            runs += 1
        else:
            check_status=False

        if runs >= max_runs:
            check_status=False
    if spinner:
        spinner.stop()

    task_state=task_status['state']
    print(f"status: {task_state}")
    if task_state in ('READY','RUNNING'):
        print(f'Task wait timed-out after {max_runs*wait_time} second')
    elif task_state=='COMPLETED':
        print('Image export completed')
    elif task_state=='UNSUBMITTED':
        print("task has not been started. task.start() might be missing")
    elif task_state=='FAILED':
        print(task_status['error_message'])

def main():
    ## ------ PARSING COMMAND LINE ARGUMENTS
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--service-user", dest='user', help="Service account user ID")
    parser.add_argument("-c", "--service-credentials", dest='credentials', help="Service account credentials file location")
    parser.add_argument("-s", "--asset-path", dest="asset_path", help="GEE asset path for saving images")
    parser.add_argument("-r", "--regions-path", dest="regions_path", help="GEE asset path for reading regions FeatureCollection")
    parser.add_argument("-e", "--export-to", dest="export_to", help="Where to export images. Valid options [toAsset | toDrive]. Default is toAsset ", choices=['toAsset','toDrive'])
    parser.add_argument("-m", "--months", dest="months", help="string of months to export '2022-11-01, 2022-10-01'. Default is to export the last fully available month in MODIS")

    args= parser.parse_args()

    if args.user:
        globals()['SNOW_SERVICE_USER']=args.user
    if args.credentials:
        globals()['SNOW_SERVICE_CREDENTIALS_FILE']=args.credentials
    if args.asset_path:
        globals()['SNOW_ASSETS_PATH=args.asset_path']=args.asset_path
    if args.regions_path:
        globals()['SNOW_REGIONS_ASSET_PATH']=args.regions_path
    if args.export_to:
        globals()['SNOW_EXPORT_TO']=args.export_to
    if args.months:
        globals()["SNOW_MONTHS_TO_EXPORT"]=[month.strip() for month in args.months.split(',')]
    
    print(f"------Starting script: {datetime.today()}-------")
    ## ------ SCRIPT SETUP ---------
    print(f"----- Initiating Setup")
    # Set script config from environmental vars
    SNOW_SERVICE_USER = set_script_config_var('SNOW_SERVICE_USER', required=True)
    SNOW_SERVICE_CREDENTIALS_FILE = set_script_config_var(
        'SNOW_SERVICE_CREDENTIALS_FILE', 
        required=True)
    SNOW_REGIONS_ASSET_PATH = set_script_config_var('SNOW_REGIONS_ASSET_PATH', required=True)
    SNOW_EXPORT_TO=set_script_config_var('SNOW_EXPORT_TO', required=True)
    SNOW_ASSETS_PATH = set_script_config_var('SNOW_ASSETS_PATH')
    SNOW_DRIVE_PATH = set_script_config_var('SNOW_DRIVE_PATH')
    SNOW_MONTHS_TO_EXPORT = set_script_config_var('SNOW_MONTHS_TO_EXPORT', parse='List')

    # Exit if no asset or drive path was set.
    if SNOW_ASSETS_PATH == None and SNOW_DRIVE_PATH == None:
        print("No Asset or Drive path provided")
        sys.exit()

    # Exit if credentials file doesn't exist in given path or as a docker secret
    SNOW_SERVICE_CREDENTIALS_FILE = check_docker_secret(SNOW_SERVICE_CREDENTIALS_FILE)
    if SNOW_SERVICE_CREDENTIALS_FILE is None:
        print("Service account credentials file was nas not found")
        sys.exit()

    # Exit if SNOW_MONTHS_TO_EXPORT environment variable was provided but has
    # incorrect values
    # TODO: Check SNOW_MONTHS_TO_EXPORT for incorrect values
    
    ## ------ GEE CONNECTION ---------
    print(f"----- Connecting to GEE")
    # Connect to GEE using service account for atutomation
    try:
        credentials = ee.ServiceAccountCredentials(SNOW_SERVICE_USER, SNOW_SERVICE_CREDENTIALS_FILE )
        ee.Initialize(credentials)    
        print("Connection successful")
    except Exception as err:
        print(err)
        sys.exit()

    ## ------ READING REGIONS ---------
    print(f"----- Reading Regions")
    # Check if "DPA_regiones_nacionales" feature collection exists else stop script
    try: 
        if check_asset_exists(SNOW_REGIONS_ASSET_PATH, "TABLE"):
            ee_territorio_nacional = ee.FeatureCollection(SNOW_REGIONS_ASSET_PATH)

    except:
        print('Could not read Regions. Terminating Script')
        sys.exit()

    ## ------ READING FROM MODIS ---------
    print(f"----- Reading from MODIS")
    # Get MODIS image Collection and take date from the last image.
    # Remove images from current month to avoid incomplete months
    # And Check if previous month has all the images for the month
    # otherwise remove the month if not complete
    try: 
        ee_MODIS_collection = (ee.ImageCollection('MODIS/006/MOD10A1'))
        ee_MODIS_collection = ee_MODIS_collection.filterDate(MODIS_MIN_MONTH, current_year_month())
        ee_MODIS_collection = rm_incomplete_months_from_ic(ee_MODIS_collection)

        # Get list of dates from image collection
        MODIS_distinct_months = get_ic_distinct_months(ee_MODIS_collection)
    except Exception as e:
        print("Couldn't read from MODIS. Terminating Script")
        print(e)
        sys.exit()

    ## ------ CHECKING IMAGES ALREADY SAVED ---------
    print(f"----- CHECKING IMAGES ALREADY SAVED")
    # Get list of months of images already saved 
    # TODO: Need an option to search assets from Drive in case exporting to Drive
    saved_assets=get_asset_list(SNOW_ASSETS_PATH, "IMAGE")
    saved_assets_months = [date[-7:]+'-01' for date in saved_assets]
    saved_assets_months.sort(reverse=True)
    print(f"Total images saved in folder: {len(saved_assets_months)}")
    if len(saved_assets_months)>0:
        print(f"first month saved: {saved_assets_months[-1]}")
        print(f"last month saved: {saved_assets_months[0]}")
  
    ## ------ DETERMINE MONTHS TO SAVE ---------
    print(f"----- Determining dates to save")
    # Save images of months in SNOW_MONTHS_TO_EXPORT otherwise save
    # the last available month in MODIS
    if SNOW_MONTHS_TO_EXPORT == None:
        try: 
            last_available = MODIS_distinct_months[0]
            months_to_save=[last_available]
        except:
            months_to_save=[]
    else:
        months_to_save=SNOW_MONTHS_TO_EXPORT

    # Check if months to save have already been saved
    months_already_saved = [month for month in months_to_save if month in saved_assets_months]
    months_to_save = [month for month in months_to_save if month not in months_already_saved]
    
    if len(months_already_saved) >= 1:
        print(f"Months already saved: {months_already_saved}")

    if len(months_to_save)==0:
        print(f"No new months to save. Exiting script")
        sys.exit()
    else:
        print(f"Months to save: {months_to_save}")

    
    ## ------ SCI, CCI CALCULATIONS ---------
    print(f"----- Calculationg SCI, CCI")
    ## ONLY RUNS IF MONTHS TO SAVE >= 1
    
    
    try:
        # Calculate and select snow and cloud bands
        ee_snow_cloud_collection = ee_MODIS_collection.map(snow_cloud_mask).select('SCI', 'CCI');
    
        # Calculate mean for last month in collection
        ee_monthly_snow_cloud_collection = imagecollection_monthly_mean(
            months_to_save, 
            ee_snow_cloud_collection
            )

    except Exception as e:
        print("Couldn't calculate SCI, CCI monthly mean. Terminating Script")
        print(e)
        sys.exit()

    ee_filtered_snow_collection = ee_monthly_snow_cloud_collection

    ## ------ EXPORT TASKS ---------
    print(f"----- Exporting Images")
    # TODO: Need to connect and export to Google drive

    print(f"Exporting to:{SNOW_EXPORT_TO}")
    export_tasks=[]
    max_exports=SNOW_MAX_EXPORTS
    for month in months_to_save:
        if max_exports==0:
            break
        else:
            max_exports -= 1
        
        ee_image = ee_monthly_snow_cloud_collection.filterDate(month).first()
        property_ym = ee_image.get('system:time_start').getInfo()
        image_name = 'MOD10A1_SCI_CCI_' + property_ym
        print(f"Exporting image: {image_name}")

        if SNOW_EXPORT_TO == "toAsset":
            task = ee.batch.Export.image.toAsset(**{
            'image': ee_image,
            'description': image_name,
            'assetId': pathlib.Path(SNOW_ASSETS_PATH, image_name).as_posix(),
            'scale': 500,
            'region': ee_territorio_nacional.geometry(),
            })
        elif SNOW_EXPORT_TO == "toDrive":
            pass

        export_tasks.append(task)

    # Start tasks 
    for task in export_tasks:
        try:
            task.start()
        except:
            print(f"Export Task failed: {task}")
    
    print("----- Checking Export Status...")
    export_running = True
    tasks_finished=[]
    while export_running:
        export_running = False
        for i, task in enumerate(export_tasks):
            if i not in tasks_finished:
                status=task.status()
                if status['state'] in ("UNSUBMITTED"):
                    print(f"{task}") 
                elif status['state'] in ("SUBMITTED", "READY","RUNNING"):
                    export_running = True
                elif status['state'] in ("COMPLETED", "CANCEL_REQUESTED", "CANCELLED"):
                    print(f"{status['description']}: {status['state']}")
                    tasks_finished.append(i)   
                elif status['state'] in ("FAILED"):
                    print(f"{status['description']}: {status['state']}")
                    print(f"error: {status['error_message']}")
                    tasks_finished.append(i)
        if export_running:
            sleep(SNOW_STATUS_CHECK_WAIT)

    print(f"----- Script finnished successfully")
    print(f"----- Finishing script: {datetime.today()}-------")

if __name__=='__main__':
    main()
