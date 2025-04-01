.PHONY: deploy requirements

ALL_SERVICES = bridge city_pass construction_work contact image modules notification

ifdef SERVICE_NAME
export SERVICE_NAME_HYPHEN=$(subst _,-,$(SERVICE_NAME))
endif

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = SERVICE_NAME=${SERVICE_NAME} docker compose
run = $(dc) run --rm -u ${UID}:${GID}
manage = $(run) dev python manage.py

help:
    # Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools
    # Install requirements and sync venv with expected state as defined in requirements.txt
	pip install -r requirements/requirements.txt
	pip install -r requirements/requirements_dev.txt

requirements:
	$(run) dev pip-compile --upgrade --output-file requirements/requirements.txt --allow-unsafe requirements/requirements.in
	echo "# Generated on: $$(date +%Y-%m-%d)" | cat - requirements/requirements.txt > tmp && mv tmp requirements/requirements.txt

	$(run) dev pip-compile --upgrade --output-file requirements/requirements_dev.txt --allow-unsafe requirements/requirements_dev.in
	echo "# Generated on: $$(date +%Y-%m-%d)" | cat - requirements/requirements_dev.txt > tmp && mv tmp requirements/requirements_dev.txt

upgrade: requirements install
    # Run 'requirements' and 'install' targets

### MAKEFILE TARGETS THAT CAN LOOP THROUGH ALL SERVICES ###
define dc_for_all
	@if [ -z "$(SERVICE_NAME)" ]; then \
	  for s in $(ALL_SERVICES); do \
		SERVICE_NAME=$$s docker compose $(1); \
	  done; \
	else \
	  SERVICE_NAME=$(SERVICE_NAME) docker compose $(1); \
	fi
endef

define run_for_all
$(call dc_for_all,run --rm -u $(UID):$(GID) $(1))
endef

migrations:
    # Create Django migrations
	$(call run_for_all,dev python manage.py makemigrations)

lintfix:
	# Execute lint fixes
	$(call run_for_all,test black /app/)
	$(call run_for_all,test ruff check /app/ --no-show-fixes --fix)
	$(call run_for_all,test isort /app/)

lint:
	# Execute lint checks
	$(call run_for_all,test ruff check /app/ --no-show-fixes)
	$(call run_for_all,test isort --diff --check /app/)

run-test:
	# Run tests
	$(call run_for_all,test)

test: run-test lint
	# Run tests & lint checks

build:
	# Build Docker images
	$(call dc_for_all,build)

push:
    # Push images to repository
	$(call dc_for_all,push)

clean:
    # Stop Docker container and remove orphans
	$(call dc_for_all,down -v --remove-orphans)

prepare-for-pr: requirements build lintfix test
    # Prepare for PR

### SINGLE SERVICE COMMANDS ###
check-service:
	# Check if SERVICE_NAME is set in environment variables
	@if [ -z "$(SERVICE_NAME)" ]; then \
		echo "ERROR: SERVICE_NAME is not set"; \
		exit 1; \
	fi

run_etl: check-service
	# Django command for the construction_work service
	$(manage) runetl

send_waste_notifications: check-service
	# Django command for the Waste service
	$(manage) sendwastenotifications

spectacular: check-service
    # Generate OpenAPI schema
	$(manage) spectacular --file /app/${SERVICE_NAME}/openapi-schema.yaml

openapi-diff: spectacular
    # Compare OpenAPI schema on acceptance with the one in the repository
	$(run) openapi-diff https://acc.app.amsterdam.nl/$(SERVICE_NAME_HYPHEN)/api/v1/openapi/ /specs/openapi-schema.yaml

migrate: check-service
    # Run Django migrations on database
	$(manage) migrate

settings: check-service
    # Show Django settings
	$(run) test python manage.py diffsettings

dev: check-service build
    # Start Django app with runserver
	$(run) --service-ports dev

app: check-service
    # Start Django app with UWsgi
	$(dc) up app

shell: check-service
    # Start Django shell
	$(manage) shell