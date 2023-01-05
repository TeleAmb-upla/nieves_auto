'''
Script to automate the calculation of SCI & CCI monthly average from the images available in the GEE cataloge.

SCI: Snow Cover Index
CCI: Cloud Cover Index

This script usess the following conventions:
- Server side variables start with ee_


'''

import ee
import geemap
from datetime import datetime
import pytz
import json
import pprint
import pathlib
from time import sleep
from yaspin import yaspin
from math import ceil

GEE_PATHPREFIX = 'projects/earthengine-legacy/assets/'
DPA_REGIONES_NACIONALES = 'users/proyectosequiateleamb/Regiones/DPA_regiones_nacional'
SAVED_IMAGES_PATH = 'users/proyectosequiateleamb/Nieves/Raster_SCI_CCI'
MODIS_MIN_MONTH = '2000-03'
UTC_TZ=pytz.timezone('UTC')

def current_year_month():
    '''
    Returns the current year and month from local machine
    '''
    return str(datetime.today().year) + "-" + str(datetime.today().month)

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

def get_asset_list(parent):
    '''List assets from an assets foler in GGE

    reference: https://github.com/spatialthoughts/projects/blob/master/ee-python/list_all_assets.py
    '''
    parent_asset = ee.data.getAsset(parent)
    parent_id = parent_asset['name']
    parent_type = parent_asset['type']
    asset_list = []
    child_assets = ee.data.listAssets({'parent': parent_id})['assets']
    for child_asset in child_assets:
        child_id = child_asset['name']
        child_type = child_asset['type']
        if child_type in ['FOLDER','IMAGE_COLLECTION']:
            # Recursively call the function to get child assets
            asset_list.extend(get_asset_list(child_id))
        else:
            asset_list.append(child_id)
    return asset_list

def check_asset_exists(asset: str):
    '''Test if feature collection is in the asset list.
    Returns True if asset is found, False if it isn't
    '''

    asset_path = pathlib.Path(asset).parent.as_posix()
    print(f"Searching for: {asset}")

    # Get list of assets in given path
    try: 
        asset_list = get_asset_list(asset_path)
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
        print(f"Processing: {format_ee_timestamp(ee_target_ym.getInfo())} - {format_ee_timestamp(ee_post_target_ym.getInfo())}")

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
    # TODO: Get config values from environment variables

    # TODO: Get for GEE service account information from Environment Variables
    
    # Connect to GEE using service account for atutomation
    service_account = "nieves-test@ee-chompitest.iam.gserviceaccount.com"
    credentials_file = 'ee-chompitest-ccb9a3676966.json'
    credentials = ee.ServiceAccountCredentials(service_account, credentials_file )
    ee.Initialize(credentials)    

    # Check if "DPA_regiones_nacionales" feature collection exists else stop script
    try: 
        if check_asset_exists(DPA_REGIONES_NACIONALES):
            ee_territorio_nacional = ee.FeatureCollection(DPA_REGIONES_NACIONALES)

    except:
        pass


    # Get MODIS image Collection and take date from the last image.
    # Remove images from current month to avoid incomplete months
    ee_MODIS_collection = (ee.ImageCollection('MODIS/006/MOD10A1'))
    ee_MODIS_collection = ee_MODIS_collection.filterDate(MODIS_MIN_MONTH, current_year_month())

    # Get list of dates from image collection
    MODIS_distinct_months = get_ic_distinct_months(ee_MODIS_collection)

    # Get list of months of images already saved 
    saved_assets=get_asset_list(SAVED_IMAGES_PATH)
    saved_assets_months = [date[-7:]+'-01' for date in saved_assets]
    saved_assets_months.sort(reverse=True)

    print(f"Total images saved in folder: {len(saved_assets_months)}")
    print(f"first month saved: {saved_assets_months[-1]}")
    print(f"last month saved: {saved_assets_months[0]}")
    # mising_months = [date for date in MODIS_distinct_months if date not in saved_assets_months]
    # Check if last available month in MODIS is already saved

    last_saved = saved_assets_months[0]
    last_available = MODIS_distinct_months[0]
    if(last_saved == last_available):
        print(f"Last available month is already saved: {last_available}")
    else:
        months_to_save=[last_available]
        print(f"Pending months: {months_to_save}")

    ## ONLY RUN IF MONTHS TO SAVE >= 1
    if len(months_to_save)>=1: 
        # Calculate and select snow and cloud bands
        ee_snow_cloud_collection = ee_MODIS_collection.map(snow_cloud_mask).select('SCI', 'CCI');

        # Calculate mean for last month in collection
        ee_monthly_snow_cloud_collection = imagecollection_monthly_mean(
            months_to_save, 
            ee_snow_cloud_collection
            )

        # Sort and get last image only in case there's more than one month processed
        ee_monthly_snow_cloud_collection = ee_monthly_snow_cloud_collection.sort(
                prop='system:time_start', 
                opt_ascending=False)

        ee_last_snow_cloud_image = ee_monthly_snow_cloud_collection.first()
        
        print("Exporting image...")
        property = ee_last_snow_cloud_image.get('system:time_start').getInfo()
        image_name = 'MOD10A1_SCI_CCI_' + property

        task = ee.batch.Export.image.toAsset(**{
        'image': ee_last_snow_cloud_image,
        'description': image_name,
        #'assetId': pathlib.Path(SAVED_IMAGES_PATH, image_name).as_posix()
        'assetId': 'projects/ee-chompitest/assets/snow/Raster_SCI_CCI/'+image_name,
        'scale': 500,
        'region': ee_territorio_nacional.geometry(),
        })

        task.start()

        print("Checking Export task status...")
        check_gee_task_status(task, spinner=False)


if __name__=='__main__':
    main()
