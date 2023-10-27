#!/bin/bash

# Check if a cron expression was provided as an argument
if [ $# -eq 0 ]; then
    echo "Please provide a cron expression as an argument"
    exit 1
fi

# Validate the cron expression using regex
if [[ $1 =~ ^([0-9]|[1-5][0-9])\ (([0-9]|[1-5][0-9])|(\*)|(\*\/[1-5][0-9]))\ (([0-9]|[1-2][0-9])|(\*)|(\*\/[1-2][0-9]))\ (([0-9]|1[0-2])|(\*)|(\*\/[1-9]))\ (([0-6])|(\*)|(\*\/[1-6]))$ ]]; then
    echo "Cron expression is valid"
else
    echo "Cron expression is not valid"
    exit 1
fi
