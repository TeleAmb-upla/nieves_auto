#!/bin/bash
# Script to create a cron job based on the schedule in the SNOW_CRON environment variable

# Get the cron time from the SNOW_CRON environment variable and strip leading/trailing quotes
cron_time=$(echo "$SNOW_CRON" | sed 's/^"\|"$//g' | sed "s/^'\|'$//g")

# Create a new cron job with the specified time and environment variables
echo "$cron_time root ( . /app/set_env.sh && /app/.venv/bin/python -u /app/snow_ipa/snow_ipa.py ) > /proc/1/fd/1 2> /proc/1/fd/2
" > /etc/cron.d/snow-crontab
chmod 644 /etc/cron.d/snow-crontab
