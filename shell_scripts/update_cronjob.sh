#!/bin/bash

# Get the cron time argument
cron_time=$1

# Save a copy of the existing SNOW_CRON environment variable
old_cron_time=$SNOW_CRON

# Validate the new cron expression
if /app/shell_scripts/cron_validate.sh "$cron_time"; then
    # Update the SNOW_CRON environment variable
    export SNOW_CRON="$cron_time"

    # Export the new list of environment variables
    source export_env.sh

    # Replace the previous cronjob
    source create_cronjob.sh

    # Check if the new cronjob is valid
    if [ $? -ne 0 ]; then
        # If the new cronjob is not valid, restore the old SNOW_CRON value
        export SNOW_CRON="$old_cron_time"
        source export_env.sh
        source create_cronjob.sh
    fi
fi
