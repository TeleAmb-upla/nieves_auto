#! /bin/bash
# Script to initiate multiple tasks

# Exporting environment variables to a intermediate script because tasks initiated by cron don't have access to them
/app/export_env.sh

# Initiationg supervisord to manage cron as a service
/usr/bin/supervisord
