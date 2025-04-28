.PHONY: deploy requirements

ALL_SERVICES = bridge city_pass construction_work contact image modules notification waste

ifdef SERVICE_NAME
export SERVICE_NAME_HYPHEN=$(subst _,-,$(SERVICE_NAME))
endif

dc = SERVICE_NAME=${SERVICE_NAME} docker compose
run = $(dc) run --rm
lint = $(run) lint uv run
manage = $(run) dev uv run python manage.py

help:
    # Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

install:
    # Install requirements on local active venv
	uv sync --active

requirements:
    # Update uv.lock file and overwrite timestamp
	$(run) dev uv lock --upgrade
	@timestamp=$$(date -u +"%Y-%m-%dT%H:%M:%SZ"); \
	sed -i '/^# Generated:/d' uv.lock; \
	sed -i "1s/^/# Generated: $${timestamp}\n/" uv.lock

upgrade: requirements install
    # Run 'requirements' and 'install' targets

### MAKEFILE TARGETS THAT CAN LOOP THROUGH ALL SERVICES ###
define dc_for_all
	@if [ -z "$(SERVICE_NAME)" ]; then \
	  for s in $(ALL_SERVICES); do \
		SERVICE_NAME=$$s docker compose $(1) || exit $$?; \
	  done; \
	else \
	  SERVICE_NAME=$(SERVICE_NAME) docker compose $(1); \
	fi
endef

lintfix:
	# Execute lint fixes
	$(lint) ruff format /app/
	$(lint) ruff check /app/ --no-show-fixes --fix

lint:
	# Execute lint checks
	$(lint) ruff format /app/ --check
	$(lint) ruff check /app/ --no-show-fixes

run-test:
	# Run tests
	$(call dc_for_all,run test)

coverage:
	# Run pytest coverage
	$(call dc_for_all,run --rm test sh -c "uv run coverage run -m pytest $$s && uv run coverage report")

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

openapi-diff-all:
	for s in $(ALL_SERVICES); do \
		SERVICE_NAME_HYPHEN=$$(printf '%s\n' "$$s" | tr '_' '-'); \
		SERVICE_NAME=$$s docker compose run --rm dev uv run python manage.py spectacular --file /app/$$s/openapi-schema.yaml;\
		SERVICE_NAME=$$s docker compose run --rm openapi-diff https://test.app.amsterdam.nl/$${SERVICE_NAME_HYPHEN}/api/v1/openapi/ /specs/openapi-schema.yaml --fail-on-incompatible || exit $$?; \
	done

prepare-for-pr: requirements build lintfix test openapi-diff-all
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

migrations: check-service
    # Run Django migrations on database
	$(manage) makemigrations

migrate: check-service
    # Run Django migrations on database
	$(manage) migrate

settings: check-service
    # Show Django settings for local
	$(manage) diffsettings

dev: check-service
    # Start Django app with runserver
	$(run) --service-ports dev

app: check-service
    # Start Django app with UWsgi
	$(dc) up app

shell: check-service
    # Start Django shell
	$(manage) shell
