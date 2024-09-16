### Builds core application
FROM python:3.11-alpine AS core
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

WORKDIR /app

# Install dependencies
RUN apk add --no-cache --virtual .build-deps build-base linux-headers

COPY requirements/requirements.txt /app/requirements/
RUN chmod 777 /app/requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements/requirements.txt

RUN addgroup -S app && adduser -S app -G app

COPY manage.py /app/
COPY uwsgi.ini /app/
COPY core /app/core
COPY /deploy /app/deploy

RUN python3 manage.py collectstatic --no-input
RUN mkdir /home/app/.azure
RUN chown app:app /home/app/.azure
USER app

### Provides development stage
FROM core AS dev

USER root
COPY requirements/requirements_dev.txt /app/requirements/
RUN pip install pip-tools
RUN pip install --no-cache-dir -r /app/requirements/requirements_dev.txt
WORKDIR /app
COPY pyproject.toml /app/

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME=/tmp

CMD ["./manage.py", "runserver", "--noreload", "0.0.0.0:8000"]

### City Pass stages
FROM core AS app-city-pass
COPY city_pass /app/city_pass

FROM dev AS dev-city-pass
COPY city_pass /app/city_pass
CMD ["./manage.py", "runserver", "--noreload", "0.0.0.0:8000"]
