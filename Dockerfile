########################
# BUILDER STAGE
########################
FROM python:3.14-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on \
    HOME=/tmp \
    TMPDIR=/tmp \
    AZURE_CONFIG_DIR=/tmp/.azure \
    COVERAGE_FILE=/tmp/.coverage \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX=/tmp/pycache \
    XDG_CACHE_HOME=/tmp/.cache \
    UV_CACHE_DIR=${XDG_CACHE_HOME}/uv \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Build-only packages
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    linux-headers

# Install dependencies, but not the project itself yet, for caching purposes
COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy application code
COPY manage.py ./
COPY uwsgi.ini ./
COPY gunicorn.conf.py ./
COPY core ./core
COPY deploy ./deploy
COPY notification ./notification

# Install dependencies
RUN uv sync --frozen

# Collect static assets
RUN DJANGO_SETTINGS_MODULE=core.settings.base uv run python manage.py collectstatic --no-input

########################
# RUNTIME STAGE
########################
FROM python:3.14-alpine AS runtime
ENV PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    TMPDIR=/tmp \
    AZURE_CONFIG_DIR=/tmp/.azure \
    COVERAGE_FILE=/tmp/.coverage \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX=/tmp/pycache \
    XDG_CACHE_HOME=/tmp/.cache \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Runtime packages
RUN apk add --no-cache \
    libheif \
    bash \
    curl

ARG APP_UID=1000
ARG APP_GID=1000

RUN addgroup -S -g ${APP_GID} app \
    && adduser -S -D -u ${APP_UID} -G app appuser \
    && mkdir -p "$AZURE_CONFIG_DIR" "$PYTHONPYCACHEPREFIX"

COPY --from=builder --chown=appuser:app /app /app
USER appuser

### Linting stage for administrative tasks
#   Needs root to write to the home dir, so we use the core image for these tasks
FROM runtime AS lint
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/
ENV UV_CACHE_DIR=${XDG_CACHE_HOME}/uv \
    UV_PROJECT_ENVIRONMENT=/app/.venv
USER root

### City Pass stages
FROM runtime AS app-city_pass
COPY city_pass /app/city_pass

### Modules stages
FROM runtime AS app-modules
COPY modules /app/modules

### Contact stages
FROM runtime AS app-contact
COPY contact /app/contact

### Construction Work stages
FROM runtime AS app-construction_work
COPY construction_work /app/construction_work

### Bridge stages
FROM runtime AS app-bridge
COPY bridge /app/bridge

### Notification stages
FROM runtime AS app-notification

### Image stages
FROM runtime AS app-image
COPY image /app/image

### Waste stages
FROM runtime AS app-waste
COPY waste /app/waste

### Survey stages
FROM runtime AS app-survey
COPY survey /app/survey
