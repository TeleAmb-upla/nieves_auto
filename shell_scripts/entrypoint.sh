#!/bin/bash
# Script to initiate scheduled tasks or run the script once
# if scheduled cron will be used and managed with supervisord

# Check if SNOW_SCHEDULE environment variable exists and has a value of Yes, True or 1 (case insensitive)
if [[ "${SNOW_SCHEDULER,,}" =~ ^(yes|true|1)$ ]]; then

    # TODO: Validate the cron expression
    # source /app/shell_scripts/validate_cron.sh "$SNOW_CRON"
    # if [ $? -ne 0 ]; then
    #    echo "Error: Invalid cron expression for SNOW_CRON"
    #    exit 1
    # fi

    # Export the environment variables using export_env.sh to set_env.sh so they can be used by the cronjob
    source /app/shell_scripts/export_env.sh

    # Create a cronjob to run the python script named snow_ipa.py
    source /app/shell_scripts/create_cronjob.sh

    # Initiating supervisord to manage cron as a service (default config + conf.d)
    /usr/bin/supervisord -c /etc/supervisor/supervisord.conf

else
    # Run the python script named main.py and redirect output to Docker's logging driver
    exec python -m snow_ipa.main

fi

