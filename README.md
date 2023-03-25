# Google Earth Engine SCI and CCI Image Export and automation

The project's main purpose is to provide a script to calculate the monthly average of SCI and CCI bands from MODIS images in Google Earth Engine (GEE). The process uses a google service account and stores the resulting images in a GEE Assets folder, a Google Drive folder, or both.

The project also provides a Docker Image and an example compose file that can be used to automate the monthly export of images.

The script can function in two ways:

1. Save images for specific months by specifying the months through a list argument
2. Save the image from the last fully available month in MODIS. If no months are specified, the script defaults to export the last fully available month.

Images already saved in the target folder(s) are skipped.

The script generates one image per month by taking the average of all the images in that month. It skips any month that is not complete. A month is considered complete if MODIS has an image of the last day of the month.

SCI: Snow Cover Index

CCI: Cloud Cover Index

## python script and Docker container arguments

The script can run directly in a console by providing the necessary arguments or as a docker image for automation.

The docker image is pre-configured to run the script automatically every day at 3:00 am (local time zone of the server). Since the script runs automatically the arguments can be passed to the docker container through environment variables.

example:
`$ python nieve_sequia_auto.py -u "<GGE user>" -c "Service account credential file>" - `

The script accepts the following arguments:

**-u or --service-user (Required)**: Google service account 'user' ID. Use the environment variable 'SERVICE_USER' for Docker container.

**-c or --service-credentials (Required)**: Path to the location of a JSON file with Google service account credentials. Use the environment variable 'SERVICE_CREDENTIALS_FILE' for Docker container.

**-e or --export-to (Optional)**: Target system to export images. Valid options [toAsset | toDrive | toAssetAndDrive]. Defaults to "toAsset" if no value is provided. Use the environment variable 'EXPORT_TO' for Docker container.

**-s or --asset-path (Conditional)**: Target path to a GEE Asset folder for saving images. Required if exporting to GEE Assets. Use the environment variable 'ASSET_PATH' for Docker container.

**-d or --drive-path (Conditional)**: Target path to a Google Drive folder for saving images. Required if exporting to Google Drive. Use the environment variable 'DRIVE_PATH' for Docker container.

**-r or --regions-path (Optional)**: GEE asset path for reading geographic regions from FeatureCollection. Defaults to "users/proyectosequiateleamb/Regiones/DPA_regiones_nacional" if not specified. Use the environment variable 'REGIONS_ASSET_PATH' for Docker container.

**-m or --months (Optional)**: String of months to export (example: '2022-11-01, 2022-10-01'). If not provided the default is to export the last fully available month in MODIS". Use the environment variable 'MONTHS_TO_EXPORT' for Docker container.

**-l or --log-level (Optional)**: Logging level ["DEBUG" | "INFO" | "WARNING" | "ERROR"]. The default value is "INFO". Use the environment variable 'LOG_LEVEL' for Docker container.

## Docker Environment Variables:

Use the following environment variables for Docker containers:

- SERVICE_USER
- SERVICE_CREDENTIALS_FILE
- EXPORT_TO
- ASSET_PATH
- DRIVE_PATH
- REGIONS_ASSET_PATH
- MONTHS_TO_EXPORT
- LOG_LEVEL
