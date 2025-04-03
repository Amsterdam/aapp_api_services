### Builds core application
FROM python:3.11-alpine AS core
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

WORKDIR /app

# Install dependencies
RUN apk add --no-cache --virtual .build-deps build-base linux-headers
RUN apk add --no-cache libheif

COPY pyproject.toml /app/pyproject.toml
RUN uv sync --no-default-groups

RUN addgroup -S app && adduser -S app -G app

COPY manage.py /app/
RUN dos2unix /app/manage.py
COPY uwsgi.ini /app/
COPY /core /app/core
COPY /deploy /app/deploy

RUN uv run python manage.py collectstatic --no-input
RUN mkdir /home/app/.azure
RUN chown app:app /home/app/.azure
USER app

### Provides development stage
FROM core AS dev

USER root
RUN uv sync --dev
WORKDIR /app

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME=/tmp

CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### City Pass stages
FROM core AS app-city_pass
COPY city_pass /app/city_pass

FROM dev AS dev-city_pass
COPY city_pass /app/city_pass
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### Modules stages
FROM core AS app-modules
COPY modules /app/modules

FROM dev AS dev-modules
COPY modules /app/modules
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### Contact stages
FROM core AS app-contact
COPY contact /app/contact

FROM dev AS dev-contact
COPY contact /app/contact
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### Construction Work stages
FROM core AS app-construction_work
COPY construction_work /app/construction_work

FROM dev AS dev-construction_work
COPY construction_work /app/construction_work
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### Bridge stages
FROM core AS app-bridge
COPY bridge /app/bridge

FROM dev AS dev-bridge
COPY bridge /app/bridge
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### Notification stages
FROM core AS app-notification
COPY notification /app/notification

FROM dev AS dev-notification
COPY notification /app/notification
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### Image stages
FROM core AS app-image
COPY image /app/image

FROM dev AS dev-image
COPY image /app/image
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]

### Waste stages
FROM core AS app-waste
COPY waste /app/waste

FROM dev AS dev-waste
COPY waste /app/waste
CMD ["uv", "run", "python", "./manage.py", "runserver", "0.0.0.0:8000"]
