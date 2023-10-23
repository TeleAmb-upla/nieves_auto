# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11.6-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
  cron \
  git \ 
  supervisor \
  wget \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/ \
  && mkdir -p /var/log/supervisor \
  && mkdir -p /var/log/snow


# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt


# Copy costum config files
COPY ./configs/supervisord.conf /etc/supervisor/conf.d/
COPY ./configs/nieves-crontab /etc/cron.d/

# Copy app
WORKDIR /app
COPY . /app

RUN chmod 0644 /etc/cron.d/nieves-crontab && \
  chmod 0744 /app/nieves_autorun.sh && \
  chmod 0744 /app/export_env.sh

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
#USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# CMD ["python", "nieve_sequia_auto.py"]

# Use supervisor to manage cron
CMD ["/app/nieves_autorun.sh"]
