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
COPY /core /app/core
COPY /deploy /app/deploy

RUN mkdir /home/app/.azure
RUN chown app:app /home/app/.azure
USER root
WORKDIR /app

### City Pass stages
FROM core AS app-city_pass
COPY city_pass /app/city_pass
RUN DJANGO_SETTINGS_MODULE=city_pass.settings.base uv run python manage.py collectstatic --no-input

### Modules stages
FROM core AS app-modules
COPY modules /app/modules
RUN DJANGO_SETTINGS_MODULE=modules.settings.base uv run python manage.py collectstatic --no-input

### Contact stages
FROM core AS app-contact
COPY contact /app/contact
RUN DJANGO_SETTINGS_MODULE=contact.settings.base uv run python manage.py collectstatic --no-input

### Construction Work stages
FROM core AS app-construction_work
COPY construction_work /app/construction_work
RUN DJANGO_SETTINGS_MODULE=construction_work.settings.base uv run python manage.py collectstatic --no-input

### Bridge stages
FROM core AS app-bridge
COPY bridge /app/bridge
RUN DJANGO_SETTINGS_MODULE=bridge.settings.base uv run python manage.py collectstatic --no-input

### Notification stages
FROM core AS app-notification
COPY notification /app/notification
RUN DJANGO_SETTINGS_MODULE=notification.settings.base uv run python manage.py collectstatic --no-input

### Image stages
FROM core AS app-image
COPY image /app/image
RUN DJANGO_SETTINGS_MODULE=image.settings.base uv run python manage.py collectstatic --no-input

### Waste stages
FROM core AS app-waste
COPY waste /app/waste
RUN DJANGO_SETTINGS_MODULE=waste.settings.base uv run python manage.py collectstatic --no-input
