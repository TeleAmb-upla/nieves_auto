#! /bin/bash
# Copies Environmental variables to a bash script file so Cron can have a copy 
# of the variables when executed
# Cron runs without knowledge or copy of environmental variables so they need to be 
# created explicitly every time cron runs

# Check if set_env.sh exists, if it does, remove it
if [ -f /app/set_env.sh ]; then
  rm /app/set_env.sh
fi

# create /app/set_env.sh and add an export for PATH
echo 'export PATH="/app/.venv/bin:$PATH"' >> /app/shell_scripts/set_env.sh

# Loop through all environment variables and export each variable that starts with SNOW_ or PYTHON to set_env.sh
for var in $(compgen -e)
do
  if [[ $var == SNOW_* || $var == PYTHON_* ]]; then
    echo "export $var=${!var}" >> /app/set_env.sh;
  fi
done

chmod 0744 /app/set_env.sh