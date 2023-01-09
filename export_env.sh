#! /bin/bash

touch /app/set_env.sh

if  [[ -v SNOW_SERVICE_USER ]]; then
  echo "export SNOW_SERVICE_USER=$SNOW_SERVICE_USER" >> /app/set_env.sh;
fi

if [[ -v SNOW_SERVICE_CREDENTIALS_FILE ]]; then
  echo "export SNOW_SERVICE_CREDENTIALS_FILE=$SNOW_SERVICE_CREDENTIALS_FILE" >> /app/set_env.sh;
fi

if [[ -v SNOW_REGIONS_ASSET_PATH ]]; then
  echo "export SNOW_REGIONS_ASSET_PATH=$SNOW_REGIONS_ASSET_PATH" >> /app/set_env.sh;
fi

if [[ -v SNOW_EXPORT_TO ]]; then
  echo "export SNOW_REGIONS_ASSET_PATH=$SNOW_EXPORT_TO" >> /app/set_env.sh;
fi

if [[ -v SNOW_ASSETS_PATH ]]; then
  echo "export SNOW_ASSETS_PATH=$SNOW_ASSETS_PATH" >> /app/set_env.sh;
fi

if [[ -v SNOW_DRIVE_PATH ]]; then
  echo "export SNOW_REGIONS_ASSET_PATH=$SNOW_DRIVE_PATH" >> /app/set_env.sh;
fi

if [[ -v SNOW_MONTHS_TO_EXPORT ]]; then
  echo "export SNOW_MONTHS_TO_EXPORT=$SNOW_MONTHS_TO_EXPORT" >> /app/set_env.sh;
fi

chmod 0744 /app/set_env.sh