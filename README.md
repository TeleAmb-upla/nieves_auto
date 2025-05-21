# Google Earth Engine SCI and CCI Image Processing Automation

This project provides a simple python package to process and export images with the monthly average of "Snow Cover Index (SCI)" and "Cloud Cover Index (CCI)" to a GEE Assets folder, a Google Drive Folder or both. Images are created using MODIS images in Google Earth Engine (GEE).

The package is designed to be used with Google Earth Engine and requires a Google service account with the necessary permissions to access the MODIS image collection and export images to GEE Assets or Google Drive. Standard GEE user accounts are currently not supported.

Users can run the package/script manually or automate the export process using a Docker container and by specifying a run frequency following cron rules.

You can find the latest version of the docker image in [Docker Hub](https://hub.docker.com/r/ericklinares/gee-nieve-sequia-auto).

## Specifying which images to export

You can specify which images to export with one of the following options:

1. Specify the images by providing a list of months.
2. Export the image from the last fully available month in MODIS. Default if no list of months is specified.

Images already saved in the target folder(s) are skipped. Currently there is no option to overwrite existing images.

> **Note:** If a list of months is specified and the script is set to run automatically. The list will attempt to export the same images in the list every time but will skip any exports after the first run since it will not try to overwrite existing images.

## Using as Python script

The export automation package/script is designed so it can be executed as a normal Python script.

The main script "snow_ipa.py" can be executed directly in the console by providing the required information as arguments or as Environment variables.

The script requires a Google service account in the appropriate JSON file format.

> Currently only Google Service accounts are supported since they provide the information for both GEE and Google Drive without having to deal with multiple authentication methods.

When running as a script, the process will run once and exit. To automate the execution of the script at regular intervals, use the Docker container version or configure your own cron job in the host machine.

example:

```bash
python src/snow_ipa/main.py -u "<GGE user>" -c "Service account credential file>" -other_arguments... 
```

## Using as Docker container

A Dockerfile and its respective image are also provided as an alternative to run the script as a one-time run or automatically at regular intervals like every day at 3:00 am (local time zone of the server).

The docker container can be configured through environment variables to provide the necessary parameters.

```bash
docker run -d -name nieve -e SNOW_USER=user@project.iam.gserviceaccount.com -e SNOW_SERVICE_CREDENTIALS_FILE=/credentials.json -v /path/to/credentials.json:/credentials.json -e SNOW_REGIONS_ASSET_PATH='path/to/featurecollection' -e SNOW_EXPORT_TO_GEE=true -e SNOW_GEE_ASSETS_PATH='path/to/save/assets' ericklinares/gee-nieve-sequia-auto:latest
```

See docker-compose.yml for an example of how to deploy using compose files.

## Script arguments

When running manually as a python script. The script accepts the following arguments:

**-u or --user (Required)**: Google service account 'user' ID. Use the environment variable 'SNOW_USER' for the Docker container.

**-c or --service-credentials (Required)**: Path to the location of a JSON file with Google service account credentials. Use the environment variable 'SNOW_SERVICE_CREDENTIALS_FILE' for the Docker container.

**--export-to-gee**: Boolean flag to export images to Google Earth Engine. Defaults to False if not provided
unless export-to-gdrive is also omitted, in this case it will default to True. Use the environment variable
'SNOW_EXPORT_TO_GEE' for the Docker container.

**--export-to-gdrive**: Boolean flag to export images to Google Drive. Defaults to False. Use the environment variable 'SNOW_EXPORT_TO_GDRIVE' for the Docker container.

**-s or --gee-assets-path (Conditional)**: Target path to a GEE Asset folder for saving images. Required if exporting to GEE Assets. Use the environment variable 'SNOW_GEE_ASSETS_PATH' for the Docker container.

**-d or --gdrive-assets-path (Conditional)**: Target path to a Google Drive folder for saving images. Required if exporting to Google Drive. Use the environment variable 'SNOW_GDRIVE_ASSETS_PATH' for the Docker container.

**-r or --regions-asset-path (Optional)**: GEE asset path for reading geographic regions from FeatureCollection. Defaults to "users/proyectosequiateleamb/Regiones/DPA_regiones_nacional" if not specified. Use the environment variable 'SNOW_REGIONS_ASSET_PATH' for the Docker container.

**-m or --months-to-export (Optional)**: String of months to export (example: '2022-11-01, 2022-10-01'). If not provided the default is to export the last fully available month in MODIS". Use the environment variable 'SNOW_MONTHS_LIST' for the Docker container.

**-l or --log-level (Optional)**: Logging level ["DEBUG" | "INFO" | "WARNING" | "ERROR"]. The default value is "INFO". Use the environment variable 'SNOW_LOG_LEVEL' for the Docker container.

**--log-file (Optional)**: Alternative path to a file where logs will be saved. Use the environment variable 'SNOW_LOG_FILE' for the Docker container.

**--enable-email (Optional)**: Enable email notifications. The default value is False. Use the environment variable 'SNOW_ENABLE_EMAIL' for the Docker container.

**--smtp-server (Optional)**: SMTP server for sending email notifications. Use the environment variable 'SNOW_SMTP_SERVER' for the Docker container.

**--smtp-port (Optional)**: SMTP server port for sending email notifications. Use the environment variable 'SNOW_SMTP_PORT' for the Docker container.

**--smtp-user (Optional)**: Username to log int to SMTP email server. Use the environment variable 'SNOW_SMTP_USER' for the Docker container.

**--smtp-password (Optional)**: Password to log int to SMTP email server. Use the environment variable 'SNOW_SMTP_PASSWORD' for the Docker container.

**--smtp-user-file (Optional)**: Path to a file containing the username to log int to SMTP email server. alternative option to --smtp-user. Overwrites --smtp-user if both are provided. Use the environment variable 'SNOW_SMTP_USERNAME_FILE' for the Docker container.

**--smtp-password-file (Optional)**: Path to a file containing the password to log int to SMTP email server. alternative option to --smtp-password. Overwrites --smtp-password if both are provided. Use the environment variable 'SNOW_SMTP_PASSWORD_FILE' for the Docker container.

**--smtp-from-address (Optional)**: Email address to use as sender. Use the environment variable 'SNOW_SMTP_FROM_ADDRESS' for the Docker container.

**--smtp-to-address (Optional)**: Email addresses to use as recipients. Accepts one or more email address separated by ',' or ';'. Multiple emails need to be enclosed in single or double quotes. e.g "user@email.com;user2@email.com". Use the environment variable 'SNOW_SMTP_TO_ADDRESS' for the Docker container.

## Docker container automatic scheduled execution

This project uses cron to schedule the execution of the snow_ipa.py script at a specified interval. Use the following environment variables to configure the scheduler

**SNOW_SCHEDULER (Optional)**: Enable the scheduler, otherwise the container will run once and exit. Valid options [True| False | Yes|No, 1|0]. The default value is False. U

**SNOW_CRON (Optional)**: Cron expression for the scheduler. The default value is "0 3 \* \* \*".

## Environment Variables

You can substitute command line arguments with the following environment variables.

- SNOW_USER
- SNOW_SERVICE_CREDENTIALS_FILE
- SNOW_EXPORT_TO_GEE
- SNOW_EXPORT_TO_GDRIVE
- SNOW_GEE_ASSETS_PATH
- SNOW_GDRIVE_ASSETS_PATH
- SNOW_REGIONS_ASSET_PATH
- SNOW_MONTHS_LIST
- SNOW_LOG_LEVEL
- SNOW_LOG_FILE
- SNOW_ENABLE_EMAIL
- SNOW_SMTP_SERVER
- SNOW_SMTP_PORT
- SNOW_SMTP_USER
- SNOW_SMTP_PASSWORD
- SNOW_SMTP_USER_FILE
- SNOW_SMTP_PASSWORD_FILE
- SNOW_SMTP_FROM_ADDRESS
- SNOW_SMTP_TO_ADDRESS

For Docker Container only:

- SNOW_SCHEDULER
- SNOW_CRON

## Important Notice about MODIS

:bell: As of May 2023, due to image availability this script has switched from using MODIS/006/MOD10A1 to MODIS/061/MOD10A1 as the primary image collection. MODIS/006/MOD10A1 is no longer being updated and the last available image is form mid February. Please refer to the official MODIS documentation for more information.

## Version history

### Version 4.0.0

:warning: Starting version 4.0.0 the following breaking changes were introduced:

- Some environment variables were renamed. Please see latest documentation for current names.
- Some console arguments were renamed. Please see latest documentation for current names.
- Users can now specify log file and path.
- the command line argument --export-to has been replaced with --export-to-gee and --export-to-gdrive explicit options.

### Version 3.0.0

:warning: Starting version 3.0.0 the following braking changes were introduced:

- Main script was renamed from "nieve_sequia.py" to "snow_ipa.py".
- All environment variables were renamed to use the prefix "SNOW\_". For example: "SERVICE_USER" was renamed to "SNOW_SERVICE_USER".
- One or more console arguments changed names.
- The automated Docker image will no longer run the script automatically. It will only run the script once and exit. Set the environment variables SNOW_SCHEDULER and SNOW_CRON to run the script automatically. This allows users to specify the execution frequency and time.

## Helpful links

- [Docker Hub image](https://hub.docker.com/r/ericklinares/gee-nieve-sequia-auto)
- [Google Earth Engine](https://earthengine.google.com/)
- [Google Earth Engine Python API](https://developers.google.com/earth-engine/python_install)
- [Google service accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Google service account credentials](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)
