# Google Earth Engine SCI and CCI Image Export and automation

## Overview

The project's main purpose is to provide a script to calculate and export images with the monthly average of "Snow Cover Index (SCI)" and "Cloud Cover Index (CCI)" using MODIS images in Google Earth Engine (GEE). The process uses a Google service account and exports the resulting images to a GEE Assets folder, a Google Drive folder, or both.

The project also provides a Dockerfile and an example Compose file that can be used to automate the monthly export of images using Dockers.
You can find the latest version of the docker image in [Docker Hub](https://hub.docker.com/r/ericklinares/gee-nieve-sequia-auto).

The script can function in two ways:

1. Save images for specific months by specifying the months through a list argument.
2. Save the image from the last fully available month in MODIS. If no months are specified, the script defaults to export the last fully available month.

Images already saved in the target folder(s) are skipped. Currently there is no option to overwrite existing images.

If a list of months is specified and set to run automatically. The list will attempt to export the same images in the list every time.

The script generates one image per month by taking the average of all the images in that month. It skips any month that is not complete. A month is considered complete if MODIS has an image of the last day of the month.

SCI: Snow Cover Index

CCI: Cloud Cover Index

## Python script and Docker container

The export automation script is designed so it can be executed as a normal Python script. A Dockerfile and its respective image are also provided as an alternative to run the script automatically every day at 3:00 am (local time zone of the server).

The main script "nieve_sequia_auto.py" can be executed directly in the console by providing the required information as arguments. In this case the script will run once and exit. Use the Docker container or configure your own cron if you want to run the script automatically multiple times.

example:

`$ python nieve_sequia_auto.py -u "<GGE user>" -c "Service account credential file>" -other_arguments... `

Or run as a docker container. The docker image is pre-configured to run the script automatically every day at 3:00 am (local time zone of the server). Since the script runs automatically the arguments can be provided to the script environment variables.

The script requires a JSON file with the Google service account credentials which can be provided to the container through a bind mount, a Docker config or a Docker secret. Preferably use a Docker Secret for security reasons.

```
$ docker run -d -name nieve -e SERVICE_USER=user@project.iam.gserviceaccount.com -e SERVICE_CREDENTIALS_FILE=/credentials.json -v /path/to/credentials.json:/credentials.json -e REGIONS_ASSET_PATH='path/to/featurecollection' -e EXPORT_TO=toAsset -e ASSETS_PATH='path/to/save/assets' ericklinares/gee-nieve-sequia-auto:latest
```

See docker-compose.yml for an example of how to deploy using compose files.

## Script arguments:

The script accepts the following arguments:

**-u or --service-user (Required)**: Google service account 'user' ID. Use the environment variable 'SERVICE_USER' for the Docker container.

**-c or --service-credentials (Required)**: Path to the location of a JSON file with Google service account credentials. Use the environment variable 'SERVICE_CREDENTIALS_FILE' for the Docker container.

**-e or --export-to (Optional)**: Target system to export images. Valid options [toAsset | toDrive | toAssetAndDrive]. Defaults to "toAsset" if no value is provided. Use the environment variable 'EXPORT_TO' for the Docker container.

**-s or --assets-path (Conditional)**: Target path to a GEE Asset folder for saving images. Required if exporting to GEE Assets. Use the environment variable 'ASSET_PATH' for the Docker container.

**-d or --drive-path (Conditional)**: Target path to a Google Drive folder for saving images. Required if exporting to Google Drive. Use the environment variable 'DRIVE_PATH' for the Docker container.

**-r or --regions-asset-path (Optional)**: GEE asset path for reading geographic regions from FeatureCollection. Defaults to "users/proyectosequiateleamb/Regiones/DPA_regiones_nacional" if not specified. Use the environment variable 'REGIONS_ASSET_PATH' for the Docker container.

**-m or --months-to-export (Optional)**: String of months to export (example: '2022-11-01, 2022-10-01'). If not provided the default is to export the last fully available month in MODIS". Use the environment variable 'MONTHS_TO_EXPORT' for the Docker container.

**-l or --log-level (Optional)**: Logging level ["DEBUG" | "INFO" | "WARNING" | "ERROR"]. The default value is "INFO". Use the environment variable 'LOG_LEVEL' for the Docker container.

**--enable-email (Optional)**: Enable email notifications. The default value is False. Use the environment variable 'ENABLE_EMAIL' for the Docker container.

**--smtp-server (Optional)**: SMTP server for sending email notifications. Use the environment variable 'SMTP_SERVER' for the Docker container.

**--smtp-port (Optional)**: SMTP server port for sending email notifications. Use the environment variable 'SMTP_PORT' for the Docker container.

**--smtp-user (Optional)**: Username to log int to SMTP email server. Use the environment variable 'SMTP_USERNAME' for the Docker container.

**--smtp-password (Optional)**: Password to log int to SMTP email server. Use the environment variable 'SMTP_PASSWORD' for the Docker container.

**--smtp-user-file (Optional)**: Path to a file containing the username to log int to SMTP email server. alternative option to --smtp-user. Overwrites --smtp-user if both are provided. Use the environment variable 'SMTP_USERNAME_FILE' for the Docker container.

**--smtp-password-file (Optional)**: Path to a file containing the password to log int to SMTP email server. alternative option to --smtp-password. Overwrites --smtp-password if both are provided. Use the environment variable 'SMTP_PASSWORD_FILE' for the Docker container.

**--from-address (Optional)**: Email address to use as sender. Use the environment variable 'FROM_ADDRESS' for the Docker container.

**--to-address (Optional)**: Email addresses to use as recipients. Accepts one or more email address separated by ',' or ';'. Use the environment variable 'TO_ADDRESS' for the Docker container.

## Docker Environment Variables:

Use the following environment variables for Docker containers:

- SERVICE_USER
- SERVICE_CREDENTIALS_FILE
- EXPORT_TO
- ASSET_PATH
- DRIVE_PATH
- REGIONS_ASSET_PATH
- MONTHS_LIST
- LOG_LEVEL
- ENABLE_EMAIL
- SMTP_SERVER
- SMTP_PORT
- SMTP_USERNAME
- SMTP_PASSWORD
- SMTP_USERNAME_FILE
- SMTP_PASSWORD_FILE
- FROM_ADDRESS
- TO_ADDRESS

## Helpful links

- [Docker Hub image](https://hub.docker.com/r/ericklinares/gee-nieve-sequia-auto)

- [Google Earth Engine](https://earthengine.google.com/)
- [Google Earth Engine Python API](https://developers.google.com/earth-engine/python_install)
- [Google service accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Google service account credentials](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)

## Important Notice

:bell: Due to image availability this script has switched from using MODIS/006/MOD10A1 to MODIS/061/MOD10A1 as the primary image collection. MODIS/006/MOD10A1 is no longer being updated and the last available image is form mid February. Please refer to the official MODIS documentation for more information.
