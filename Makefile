.PHONY: deploy requirements

ifndef SERVICE_NAME
$(error SERVICE_NAME is not set)
endif

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = SERVICE_NAME=${SERVICE_NAME} docker compose
run = $(dc) run --rm -u ${UID}:${GID}
manage = $(run) dev python manage.py

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip install -r requirements/requirements.txt
	pip install -r requirements/requirements_dev.txt

requirements:                       ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	# The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	# https://stackoverflow.com/questions/58843905
	$(run) dev pip-compile --upgrade --output-file requirements/requirements.txt --allow-unsafe requirements/requirements.in
	$(run) dev pip-compile --upgrade --output-file requirements/requirements_dev.txt --allow-unsafe requirements/requirements_dev.in

shell:                              ## Start Django shell
	$(manage) shell

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:                         ## Make Django migrations
	$(manage) makemigrations

migrate:                            ## Apply Django migrations to database
	$(manage) migrate

dev:                                ## Start Django app in development mode
	$(run) --service-ports dev

lintfix:                            ## Execute lint fixes
	$(run) test black /app/
	$(run) test ruff check /app/ --no-show-fixes --fix
	$(run) test isort /app/

lint:                               ## Execute lint checks
	$(run) test ruff check /app/ --no-show-fixes
	$(run) test isort --diff --check /app/

run-test:                           ## Run tests
	$(run) test

test: run-test lint                 ## Run tests & lint checks

app:                                ## Start Django app via uWSGI
	$(dc) up app

build:                              ## Build images
	$(dc) build

push:                               ## Push images to repository
	$(dc) push

clean:                              ## Stop Docker container and remove orphans
	$(dc) down -v --remove-orphans

settings:                           ## Print Django settings
	$(run) test python manage.py diffsettings

run_etl:
	$(manage) runetl
