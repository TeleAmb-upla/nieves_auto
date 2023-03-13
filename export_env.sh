#! /bin/bash
# Copies Environmental variables to a bash script file so Cron can have a copy 
# of the variables when executed
# Cron runs without knowledge or copy of environmental variables so they need to be 
# created explicitly every time cron runs

touch /app/set_env.sh

if  [[ -v SERVICE_USER ]]; then
  echo "export SERVICE_USER=$SERVICE_USER" >> /app/set_env.sh;
fi

if [[ -v SERVICE_CREDENTIALS_FILE ]]; then
  echo "export SERVICE_CREDENTIALS_FILE=$SERVICE_CREDENTIALS_FILE" >> /app/set_env.sh;
fi

if [[ -v REGIONS_ASSET_PATH ]]; then
  echo "export REGIONS_ASSET_PATH=$REGIONS_ASSET_PATH" >> /app/set_env.sh;
fi

if [[ -v EXPORT_TO ]]; then
  echo "export EXPORT_TO=$EXPORT_TO" >> /app/set_env.sh;
fi

if [[ -v ASSETS_PATH ]]; then
  echo "export ASSETS_PATH=$ASSETS_PATH" >> /app/set_env.sh;
fi

if [[ -v DRIVE_PATH ]]; then
  echo "export DRIVE_PATH=$DRIVE_PATH" >> /app/set_env.sh;
fi

if [[ -v MONTHS_TO_EXPORT ]]; then
  echo "export MONTHS_TO_EXPORT=$MONTHS_TO_EXPORT" >> /app/set_env.sh;
fi

chmod 0744 /app/set_env.sh