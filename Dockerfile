### Stage 1: app
FROM python:3.11-alpine as app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

WORKDIR /app

COPY requirements.txt /app/
COPY requirements_dev.txt /app/
COPY manage.py /app/
COPY uwsgi.ini /app/
COPY main_application /app/main_application
COPY city_pass /app/city_pass
COPY /deploy /app/deploy

ENV PYTHONPATH=/app/city_pass

# Install dependencies
RUN apk add --no-cache --virtual .build-deps build-base linux-headers \
    # For building uWSGI binary
    && apk add --no-cache gcc python3-dev \
    # && apk add --no-cache \
        #  bash netcat-openbsd procps \
        #  postgresql15-client \
        #  curl \
        #  libffi-dev libheif-dev libde265-dev \
        #  pcre pcre-dev mailcap \
        #  gcc python3-dev musl-dev \
        #  g++ \
    && apk del .build-deps

RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements_dev.txt
RUN addgroup -S app && adduser -S app -G app
RUN python3 manage.py collectstatic --no-input

RUN mkdir /home/app/.azure
RUN chown app:app /home/app/.azure
USER app

### Stage 2: dev
FROM app as dev

USER root
WORKDIR /app
USER app

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME /tmp

CMD ["./manage.py", "runserver", "0.0.0.0:8000"]

### Stage 3: tests
FROM dev as tests

# TODO: Add coverage file, and black linting here
