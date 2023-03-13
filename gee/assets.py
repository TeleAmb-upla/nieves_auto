import logging
import pathlib
import sys
import ee
from utils import logs

# Constants. Used as Defaults in case no alternative is provided.
GEE_PATHPREFIX = 'projects/earthengine-legacy/assets/'

def get_asset_list(parent:str, asset_type=None):
    '''
    Gets list assets from an assets folder in GGE 

    Args: 
        parent: path to the parent folder of the assets
        asset_type: indicats asset types to list.  

    reference: https://github.com/spatialthoughts/projects/blob/master/ee-python/list_all_assets.py
    '''
    try:
        parent_asset = ee.data.getAsset(parent)
        # If not a folder raise an error
        if parent_asset['type'] not in ['FOLDER','IMAGE_COLLECTION']:
            raise
        
    except:
        logs.print_log(f"Can't find assets folder: {parent}", 'ERROR')
        sys.exit(0)
        #raise
    parent_id = parent_asset['name']
    parent_type = parent_asset['type']
    asset_list = []
    try:
        child_assets = ee.data.listAssets({'parent': parent_id})['assets']
    except:    
        logs.print_log(f"Can't list objects in: {parent}", 'WARNING')
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
    '''Test if an asset exists in GEE Assets for the user.

    Args:
        asset: path to the asset in GEE 
        asset_type: indicates type of asset expected
    
    Returns:
        Returns True if asset is found, False if it isn't
    '''

    asset_path = pathlib.Path(asset).parent.as_posix()
    logging.debug(f"Searching for: {asset}")

    # Get list of assets in given path
    try: 
        asset_list = get_asset_list(asset_path, asset_type=asset_type)
        logging.debug('Found {} assets'.format(len(asset_list)))

    except:
        logs.print_log("Asset list could not be retreived", "WARNING")
        return False

    # Check if asset is in asset list
    asset_found = False
    for asset_x in asset_list:
        if GEE_PATHPREFIX + asset == asset_x:
            asset_found = True

    logging.debug(f"Asset successfully found: {asset_found}")
    return asset_found

def check_folder_exists(path):
    try:
        asset = ee.data.getAsset(path)
        if asset:
            return asset['type'] in ['FOLDER','IMAGE_COLLECTION']
    except:
        print("Can't find folder")
        return False

