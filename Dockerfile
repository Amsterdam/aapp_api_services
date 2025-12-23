### Builds core application
FROM python:3.11-alpine AS core
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME=/tmp \
    TMPDIR=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX=/tmp/pycache
WORKDIR /app

# Install dependencies
RUN apk add --no-cache --virtual .build-deps build-base linux-headers
RUN apk add --no-cache \
    libheif \
    bash \
    curl

COPY pyproject.toml /app/pyproject.toml
RUN uv sync

RUN addgroup -S app && adduser -S app -G app

COPY manage.py /app/
RUN dos2unix /app/manage.py
COPY uwsgi.ini /app/
COPY gunicorn.conf.py /app/
COPY /core /app/core
COPY /deploy /app/deploy

RUN DJANGO_SETTINGS_MODULE=core.settings.base uv run python manage.py collectstatic --no-input
RUN mkdir /home/app/.azure
RUN chown app:app /home/app/.azure
USER root
WORKDIR /app

### City Pass stages
FROM core AS app-city_pass
COPY city_pass /app/city_pass

### Modules stages
FROM core AS app-modules
COPY modules /app/modules

### Contact stages
FROM core AS app-contact
COPY contact /app/contact

### Construction Work stages
FROM core AS app-construction_work
COPY construction_work /app/construction_work

### Bridge stages
FROM core AS app-bridge
COPY bridge /app/bridge

### Notification stages
FROM core AS app-notification
COPY notification /app/notification

### Image stages
FROM core AS app-image
COPY image /app/image

### Waste stages
FROM core AS app-waste
COPY waste /app/waste

### Waste stages
FROM core AS app-survey
COPY survey /app/survey
