.PHONY: manifests deploy

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = docker-compose
run = $(dc) run --rm -u ${UID}:${GID}

ENVIRONMENT ?= local
HELM_ARGS = oci://${REGISTRY}/amsterdam/helm-generic-application --version 1.12.1  \
	-f manifests/values.yaml \
	-f manifests/env/${ENVIRONMENT}.yaml \
	--set image.tag=${VERSION}

REGISTRY ?= localhost:5000
REPOSITORY ?= Amsterdam-App/aapp-construction-work
VERSION ?= latest

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements_dev.txt

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	## The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	## https://stackoverflow.com/questions/58843905
	pip-compile --upgrade --output-file requirements.txt --allow-unsafe requirements.in
	pip-compile --upgrade --output-file requirements_dev.txt --allow-unsafe requirements_dev.in

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:
	$(run) dev python manage.py makemigrations

migrate:
	$(run) dev python manage.py migrate

build:
	$(dc) build

dev:
	$(run) --service-ports dev

app:
	$(dc) up app

test:
	$(dc) run --rm -u ${UID}:${GID} test

push:
	$(dc) push

# Move to aapp_infra_deployments
manifests:
	@helm template construction-work $(HELM_ARGS) $(ARGS)

# Move to aapp_infra_deployments
deploy: manifests
	helm upgrade --install construction-work $(HELM_ARGS) $(ARGS)

clean:
	$(dc) down -v --remove-orphans
