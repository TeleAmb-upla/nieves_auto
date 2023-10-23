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

if [[ -v MONTHS_LIST ]]; then
  echo "export MONTHS_LIST=$MONTHS_LIST" >> /app/set_env.sh;
fi

if [[ -v ENABLE_EMAIL ]]; then
  echo "export ENABLE_EMAIL=$ENABLE_EMAIL" >> /app/set_env.sh;
fi

if [[ -v SMTP_SERVER ]]; then
  echo "export SMTP_SERVER=$SMTP_SERVER" >> /app/set_env.sh;
fi

if [[ -v SMTP_PORT ]]; then
  echo "export SMTP_PORT=$SMTP_PORT" >> /app/set_env.sh;
fi

if [[ -v SMTP_USERNAME ]]; then
  echo "export SMTP_USERNAME=$SMTP_USERNAME" >> /app/set_env.sh;
fi

if [[ -v SMTP_PASSWORD ]]; then
  echo "export SMTP_PASSWORD=$SMTP_PASSWORD" >> /app/set_env.sh;
fi


if [[ -v SMTP_USERNAME_FILE ]]; then
  echo "export SMTP_USERNAME_FILE=$SMTP_USERNAME_FILE" >> /app/set_env.sh;
fi

if [[ -v SMTP_PASSWORD_FILE ]]; then
  echo "export SMTP_PASSWORD_FILE=$SMTP_PASSWORD_FILE" >> /app/set_env.sh;
fi

if [[ -v FROM_ADDRESS ]]; then
  echo "export FROM_ADDRESS=$FROM_ADDRESS" >> /app/set_env.sh;
fi

if [[ -v TO_ADDRESS ]]; then
  echo "export TO_ADDRESS=$TO_ADDRESS" >> /app/set_env.sh;
fi

if [[ -v LOG_LEVEL ]]; then
  echo "export LOG_LEVEL=$LOG_LEVEL" >> /app/set_env.sh;
fi

if [[ -v LOG_FILE ]]; then
  echo "export LOG_FILE=$LOG_FILE" >> /app/set_env.sh;
fi



chmod 0744 /app/set_env.sh