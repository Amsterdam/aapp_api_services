.PHONY: deploy requirements

# ifndef APP_NAME
# $(error APP_NAME is not set)
# endif
# app-name = ${APP_NAME}

app-name ?= city-pass
app-name-snake = $(subst -,_,$(app-name))

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = docker compose
run = $(dc) run --rm -u ${UID}:${GID}
manage = $(run) dev-$(app-name) python manage.py

REGISTRY ?= localhost:5000
REPOSITORY ?= Amsterdam-App/aapp-construction-work
VERSION ?= latest

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements/requirements_dev.txt

requirements:                       ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	# The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	# https://stackoverflow.com/questions/58843905
	$(run) dev-$(app-name) pip-compile --upgrade --output-file requirements/requirements.txt --allow-unsafe requirements/requirements.in
	$(run) dev-$(app-name) pip-compile --upgrade --output-file requirements/requirements_dev.txt --allow-unsafe requirements/requirements_dev.in

shell:                              ## Start Django shell
	$(manage) shell

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:                         ## Make Django migrations
	$(manage) makemigrations

migrate:                            ## Apply Django migrations to database
	$(manage) migrate

dev:                                ## Start Django app in development mode
	$(run) --service-ports dev-$(app-name)

lintfix:                            ## Execute lint fixes
	$(run) test-$(app-name) black /app/$(app-name-snake)
	$(run) test-$(app-name) autoflake /app/$(app-name-snake) --recursive --in-place --remove-unused-variables --remove-all-unused-imports --quiet
	$(run) test-$(app-name) isort /app/$(app-name-snake)

lint:                               ## Execute lint checks
	$(run) test-$(app-name) autoflake /app/$(app-name-snake) --check --recursive --quiet
	$(run) test-$(app-name) isort --diff --check /app/$(app-name-snake)

test: lint                          ## Run tests
	$(run) test-$(app-name)

app:                                ## Start Django app via uWSGI
	$(dc) up app-$(app-name)

build:                              ## Build images
	$(dc) build

push:                               ## Push images to repository
	$(dc) push

clean:                              ## Stop Docker container and remove orphans
	$(dc) down -v --remove-orphans
