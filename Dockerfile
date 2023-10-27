FROM python:3.11.6-slim-bookworm as builder

RUN pip install poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11.6-slim-bookworm as runtime

## Install system dependencies
# using supervisor to run cron in the background as service
RUN apt-get update && apt-get install -y \
    cron \
    #   git \ 
    supervisor \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/ \
    && mkdir -p /var/log/supervisor \
    && mkdir -p /var/log/snow

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Copy virtual environment from the builder stage
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy costum config files
COPY ./configs/supervisord.conf /etc/supervisor/conf.d/
# COPY ./configs/nieves-crontab /etc/cron.d/

# Copy app
WORKDIR /app
COPY . /app

# RUN chmod 0644 /etc/cron.d/nieves-crontab && \
# chmod 0744 /app/nieves_autorun.sh && \
RUN chmod 0744 /app/shell_scripts/*.sh

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
#USER appuser


# Use supervisor to manage cron
CMD ["/app/shell_scripts/entrypoint.sh"]

# forward logging to docker log collector
#* * * * *  python3 /app/test.py >>/tmp/out.log 2>/tmp/err.log