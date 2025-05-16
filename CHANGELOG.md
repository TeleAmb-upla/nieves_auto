# CHANGELOG

<!-- version list -->

## v4.0.0

This version introduces significant refactoring to the code and updates dependant packages to their latest version as of this date.

### Features

- Users can now specify alternative log file and path.

### Breaking Changes

- Primary script was renamed from snow_ipa.snow_ipa.py to snow_ipa.main.py
- Some environment variables were renamed. Please see latest documentation for current names
- Some console arguments were renamed. Please see latest documentation for current names

### Build System

- deps: bump earthengine-api to v1.5.15
- deps: bump google-api-python-client to v2.169.0
- deps: add prettytable v3.16.0 to improve reporting of exports
- deps: add jinja2 v3.1.6 to improve email template rendering

## v3.0.0

### Breaking Changes

- Main script was renamed from "nieve_sequia.py" to "snow_ipa.py".
- All environment variables were renamed to use the prefix "SNOW\_". For example: "SERVICE_USER" was renamed to "SNOW_SERVICE_USER".
- One or more console arguments changed names.
- The automated Docker image will no longer run the script automatically. It will only run the script once and exit. Set the environment variables SNOW_SCHEDULER and SNOW_CRON to run the script automatically. This allows users to specify the execution frequency and time.
