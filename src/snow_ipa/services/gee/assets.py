import logging
import pathlib
import re
import ee
from ee import data as ee_data

# cSpell:enableCompoundWords

logger = logging.getLogger(__name__)
# Constants. Used as Defaults in case no alternative is provided.
GEE_LEGACY_PATHPREFIX = "projects/earthengine-legacy/assets/"


def get_asset_list(parent: str, asset_type=None, recursive: bool = False):
    """
    lists assets from an assets folder or Image Collection in GEE. User can specify what type of assets to list.

    Args:
        parent: path to the parent folder of the assets
        asset_type: indicats asset types to list.
        recursive: Recursively search for assets in sub-folders

    reference: https://github.com/spatialthoughts/projects/blob/master/ee-python/list_all_assets.py
    """

    if isinstance(asset_type, str):
        asset_type = [asset_type]
    if asset_type is None:
        asset_type = []

    # Get information of path to list
    try:
        parent_asset = ee_data.getAsset(parent)
        parent_id = parent_asset["name"]
        parent_type = parent_asset["type"]
        # If path is not a folder or image collection raise an error
        if parent_type not in ["FOLDER", "IMAGE_COLLECTION"]:
            raise ValueError("Path provided is not a Folder or Image Collection")
    except ValueError as e:
        raise
    except Exception as e:
        logger.error(f"Can't find assets folder")
        raise

    try:
        asset_list = []
        child_assets = ee_data.listAssets({"parent": parent_id})["assets"]
        if type(child_assets) != list:
            raise Exception(
                f"Expecting a 'list' of assets but got '{type(asset_list)}' instead"
            )
    except Exception as e:
        logger.warning(f"Can't list objects in: {parent}")
        logger.warning(e)
        raise

    # Get assets from list
    for child_asset in child_assets:
        child_id = child_asset["name"]
        child_type = child_asset["type"]
        # print(f"{child_id}:{child_type}")
        if child_type in ["FOLDER", "IMAGE_COLLECTION"]:
            # Recursively call the function to get child assets
            if recursive:
                asset_list.extend(get_asset_list(child_id))
        else:
            if child_type in asset_type or len(asset_type) == 0:
                asset_list.append(child_id)
    return asset_list


def check_asset_exists(asset: str, asset_type=None):
    """Test if an asset exists in GEE Assets for the user.

    Args:
        asset: path to the asset in GEE
        asset_type: indicates type of asset expected

    Returns:
        Returns True if asset is found, False if it isn't
    """

    asset_path = pathlib.Path(asset).parent.as_posix()
    try:
        asset_found = False
        # Get list of assets in given path
        asset_list = get_asset_list(asset_path, asset_type=asset_type)
        if asset_list and isinstance(asset_list, list):
            for asset_i in asset_list:
                if (GEE_LEGACY_PATHPREFIX + asset == asset_i) or (asset == asset_i):
                    asset_found = True
                    break
        return asset_found

    except Exception as e:
        return False


def check_folder_exists(path):
    """
    Check if a folder or image collection exists in Google Earth Engine.

    Args:
        path (str): The path of the asset to check.

    Returns:
        bool: True if the asset exists and is a folder or image collection, False otherwise.
    """
    try:
        asset = ee_data.getAsset(path)
        if asset:
            return asset["type"] in ["FOLDER", "IMAGE_COLLECTION"]
    except Exception as e:
        logger.warning(e)
        return False


def get_trailing_ym(assets_list: list) -> list:
    """
    Given a list of asset names, returns a sorted list of months in the format of YYYY-MM
    for each asset that ended with a trailing YYYY-MM in the asset name.

    Args:
        assets_list (list): A list of asset names.

    Returns:
        list: A list of trailing year-month-day strings in descending order.
    """
    # Get list of months from assets names and sort

    assets_months: list[str] = []
    if isinstance(assets_list, list):
        # Verify that assets end with YYYY-MM
        for asset in assets_list:
            year_month = asset[-7:]
            if re.fullmatch(r"\d{4}-\d{2}", year_month):
                month = int(year_month[5:])
                if month >= 1 and month <= 12:
                    assets_months.append(year_month)

    assets_months.sort(reverse=True)
    return assets_months
