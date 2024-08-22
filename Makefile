.PHONY: deploy requirements

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = docker compose
run = $(dc) run --rm -u ${UID}:${GID}
manage = $(run) dev python manage.py

REGISTRY ?= localhost:5000
REPOSITORY ?= Amsterdam-App/aapp-construction-work
VERSION ?= latest

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements_dev.txt

requirements:                       ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	## The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	## https://stackoverflow.com/questions/58843905
	$(run) dev pip-compile --upgrade --output-file requirements/requirements.txt --allow-unsafe requirements/requirements.in
	$(run) dev pip-compile --upgrade --output-file requirements/requirements_dev.txt --allow-unsafe requirements/requirements_dev.in

shell:
	$(manage) shell

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:
	$(manage) makemigrations

migrate:
	$(manage) migrate

build:
	$(dc) build

dev:
	$(run) --service-ports dev

app:
	$(dc) up app

test:
	$(run) test

push:
	$(dc) push

clean:
	$(dc) down -v --remove-orphans
