### Builds core application
FROM python:3.14-alpine AS core
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV APP_TMPDIR=/tmp
ENV HOME=${APP_TMPDIR} \
    TMPDIR=${APP_TMPDIR} \
    AZURE_CONFIG_DIR=${APP_TMPDIR}/.azure \
    XDG_CACHE_HOME=${APP_TMPDIR}/.cache \
    COVERAGE_FILE=${APP_TMPDIR}/.coverage \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX=${APP_TMPDIR}/pycache
ENV UV_CACHE_DIR=${XDG_CACHE_HOME}/uv
WORKDIR /app

# Install dependencies
RUN apk add --no-cache --virtual .build-deps build-base linux-headers
RUN apk add --no-cache \
    libheif \
    bash \
    curl

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
RUN uv sync --frozen

ARG APP_UID=1000
ARG APP_GID=1000
RUN addgroup -S -g ${APP_GID} app \
    && adduser -S -D -u ${APP_UID} -G app appuser

COPY manage.py /app/
RUN dos2unix /app/manage.py
COPY uwsgi.ini /app/
COPY gunicorn.conf.py /app/
COPY /core /app/core
COPY /deploy /app/deploy

RUN DJANGO_SETTINGS_MODULE=core.settings.base uv run python manage.py collectstatic --no-input
RUN mkdir -p "$AZURE_CONFIG_DIR" "$PYTHONPYCACHEPREFIX" "$UV_CACHE_DIR" \
    && chown -R appuser:app "$AZURE_CONFIG_DIR" "$PYTHONPYCACHEPREFIX" "$XDG_CACHE_HOME"
USER appuser
WORKDIR /app
COPY notification /app/notification

### Core stages for administrative tasks
FROM core AS app-core
USER root

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

### Image stages
FROM core AS app-image
COPY image /app/image

### Waste stages
FROM core AS app-waste
COPY waste /app/waste

### Survey stages
FROM core AS app-survey
COPY survey /app/survey
