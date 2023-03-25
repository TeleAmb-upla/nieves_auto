from  pathlib import Path
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils import logs

def get_folder_id(drive_service, path:str, parent:str=None):
    '''
    Gets the id of the folder from a given path.
    
    Args:
        drive_service: Google drive API service
        path: path of the folder to get id from
        parent: id of the parent folder if known

    Returns:
        Returns the id of the folder or None if path doesn't exist. 
    '''
    # Parse path 
    path_tuple = Path(path).parts
    current_folder=path_tuple[0]

    # Build query string
    query = "mimeType = 'application/vnd.google-apps.folder'"
    query = query +" "+ f"and name = '{current_folder}'"
    if parent:
        query = query + " " + f"and '{parent}' in parents"
    
    # Call the Drive v3 API
    try: 
        items = []
        page_token=None
        while True:
            results = drive_service.files().list(
                q = query,
                pageSize=100, 
                pageToken=page_token,
                fields="nextPageToken, files(id, name, parents)"
                ).execute()
            items.extend(results.get('files', []))
            page_token= results.get('nextPageToken', None)
            if page_token is None:
                break
        if len(items)>1 and parent is None:
            # This should only happen when searching for folders in root.
            # because we haven't found a way to specify root as parent
            items = [item for item in items if "parents" not in item.keys()]
                
        # Error control in case we end up with an empty list 
        if len(items)>=1:
            current_folder_id=items[0]['id']
        else:
            # Stop and return
            return None

    except HttpError as error:
        logging.warning(error)
        # Stop and return
        return None
    
    target_folder_id = current_folder_id 

    # Recursive call if path if not yet in target folder 
    if len(path_tuple)>1 and current_folder_id:
        target_folder_id=get_folder_id(drive_service=drive_service,
                           path="/".join(path_tuple[1:]),
                           parent=current_folder_id
                     )
    
    return target_folder_id

def drive_list_files(drive_service, path:str=None, folder_id:str=None, 
                     asset_type=None, recursive:bool=False):
    '''
    List all files and folders in google drive given a path or folder_id

    Args:
        drive_service: Google drive API service
        path: path in Google drive
        folder_id: Unique ID of a folder in google drive. If both path and folder_id are set, the ID of the given path must match the given folder_id
        asset_type: List or single string indicating the type of files to consider
        recursive: If true, will also list files in sub-folders 

    Returns:
        returns a list with the names of the files found in the given path or folder id
    '''
    # if asset_type is a single item of type string. Convert to list
    if not asset_type:
        asset_type=[]
    elif type(asset_type) == str:
        asset_type=[asset_type]
        
    
    if folder_id and path:
        path_folder_id = get_folder_id(drive_service=drive_service,path=path)
        if folder_id!=path_folder_id:
            print("Error, folder_id and path provided don't match")
            return None
    elif folder_id:
        try:
            item=drive_service.files().get(fileId=folder_id).execute()
            if item['mimeType']!='application/vnd.google-apps.folder':
                print('Error: not a folder')
                return None
        except HttpError as err:
            print(err)
            return None

    elif path:
        # Get folder ID
        folder_id=get_folder_id(drive_service=drive_service,path=path)
        if not folder_id:
            print("Error, folder not found")
            return None

    else:
        # if folder_id and path are None, list everything from root folder
        folder_id=None
    
    # build query string
    if folder_id:
        query = f"'{folder_id}' in parents"
    else:
        # list everything
        query = None
        
    # print(f"query: {query}")
    
    try: 
        asset_list = []
        child_assets = []
        page_token=None
        while True:
            results = drive_service.files().list(
                q = query,
                pageSize=100, 
                pageToken=page_token,
                fields="nextPageToken, files(id, name, parents, mimeType)"
                ).execute()
            child_assets.extend(results.get('files', []))
            page_token= results.get('nextPageToken', None)
            if page_token is None:
                break
        # print(f"assets_found: {len(child_assets)}")
    except HttpError as error:
        print(f"Can't list objects in: {path}")
        print(error)

    # iterate over items found. Jump into next folder if item is folder
    for child_asset in child_assets:
        child_id = child_asset['id']
        child_name = child_asset['name']
        child_type = child_asset['mimeType']
        # print(f"{child_name}:{child_type}")
        if child_type in ['application/vnd.google-apps.folder']:
            if recursive:
                # Recursively call function to jump in next folder
                grandchild_assets = drive_list_files(
                    drive_service=drive_service,
                    folder_id=child_id
                    )
                grandchild_assets = [child_name+"/"+item for item in grandchild_assets]
                asset_list.extend(grandchild_assets)
            else:
                pass
        else:
            # if asset_type is provided, return only items of that type 
            if child_type in asset_type or len(asset_type) == 0:
                asset_list.append(child_name)
            else:
                pass
    return asset_list

def check_asset_exists(drive_service, asset: str, asset_type=None):
    '''Test if an asset exists in Google Drive.

    Args:
        drive_service: Google drive API service
        asset: path to the asset in Google Drive
        asset_type: indicates type of asset expected
    
    Returns:
        Returns True if asset is found, False if it isn't
    '''
    asset_path = Path(asset).parent.as_posix()
    file_name = Path(asset).name
    logging.debug(f"Searching for: {asset}")

    # Get list of assets in given path
    try: 
        asset_list = drive_list_files(
            drive_service = drive_service,
            path=asset_path, 
            asset_type=asset_type)
        logging.debug('Found {} assets'.format(len(asset_list)))

    except:
        logging.warning("Asset list could not be retreived")
        return None

    # Check if asset is in asset list
    
    asset_found = False
    for asset_x in asset_list:
        if file_name == asset_x:
            asset_found = True


    logging.debug(f"Asset successfully found: {asset_found}")

    return asset_found

def check_folder_exists(drive_service, path:str)->bool:
    folder_id=get_folder_id(
        drive_service=drive_service,
        path=path
    )
    if folder_id:
        return True
    else:
        return False

# Remove sufix
def remove_extension(file):
    file=Path(file)
    return file.with_name(file.stem).as_posix()

def get_asset_list(drive_service, path, asset_type=None):
    '''
    List files in similar format to GEE Assets
    '''
    # Convert to list if only provides one asset_type as a string
    if type(asset_type==str):
        asset_type = [asset_type]
    
    # Convert IMAGE type to something Google Drive can understand
    drive_asset_type = ['image/tiff' for type in asset_type if type=='IMAGE' ]

    # Get list of assets
    asset_list = drive_list_files(
        drive_service=drive_service,
        path=path,
        asset_type=drive_asset_type
    )

    # Remove sufix of file names
    if asset_list:
        asset_list = list(map(remove_extension, asset_list))
    return asset_list

def main():
    pass

if __name__=="__main__":
    main()
    