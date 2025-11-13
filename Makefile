.PHONY: deploy requirements

ALL_SERVICES = bridge city_pass construction_work contact image modules notification waste survey

ifdef SERVICE_NAME
export SERVICE_NAME_HYPHEN=$(subst _,-,$(SERVICE_NAME))
endif

ifdef TARGET_MIGRATION
export TARGET_MIGRATION_APP=$(SERVICE_NAME)
endif

API_AUTH_TOKENS ?= insecure-token

dc = SERVICE_NAME=${SERVICE_NAME} docker compose
run = $(dc) run --rm
lint = $(run) lint uv run
manage = $(run) dev uv run python manage.py

help:
    # Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

lock-packages:
    # Update uv.lock file and overwrite timestamp
	$(lint) uv lock --upgrade
	@timestamp=$$(date -u +"%Y-%m-%dT%H:%M:%SZ"); \
	sed -i '/^# Generated:/d' uv.lock; \
	sed -i "1s/^/# Generated: $${timestamp}\n/" uv.lock; \

pip-freeze:
    # Run pip-freeze for human readable requirements.txt
	$(lint) uv pip freeze > requirements.txt
	@timestamp=$$(date -u +"%Y-%m-%dT%H:%M:%SZ"); \
	sed -i "1s/^/# Generated: $${timestamp}\n/" requirements.txt;

requirements: lock-packages build pip-freeze
    # Update dependencies and generate requirements.txt

### MAKEFILE TARGETS THAT CAN LOOP THROUGH ALL SERVICES ###
# Interprets code 5 (no tests found) as 0 (success)
define dc_for_all
	@if [ -z "$(SERVICE_NAME)" ]; then \
	  for s in $(ALL_SERVICES); do \
		SERVICE_NAME=$$s docker compose $(1);  \
	    status=$$?; if [ $$status -ne 0 ] && [ $$status -ne 5 ]; then exit $$status; fi; \
	  done; \
	else \
	  s=$$SERVICE_NAME; \
	  SERVICE_NAME=$$s docker compose $(1);  \
      status=$$?; if [ $$status -ne 0 ] && [ $$status -ne 5 ]; then exit $$status; fi; \
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
	$(call dc_for_all,run --rm test sh -c "uv run coverage run -m pytest $$s core && uv run coverage report")

integration-test:
	# Run integration tests
	# Don't forget to set the API_AUTH_TOKENS environment variable!
	$(call dc_for_all,run --rm --env API_AUTH_TOKENS='$(API_AUTH_TOKENS)' dev uv run pytest -m integration)

test: coverage lint
	# Run tests (via coverage), coverage and lint checks

build:
	# Build Docker images
	$(call dc_for_all,build)

push:
    # Push images to repository
	$(call dc_for_all,push)

clean:
    # Stop Docker container and remove orphans
	$(call dc_for_all,down -v --remove-orphans)

openapi-diff:
	@if [ -z "$(SERVICE_NAME)" ]; then \
	  for s in $(ALL_SERVICES); do \
		SERVICE_NAME_HYPHEN=$$(printf '%s\n' "$$s" | tr '_' '-'); \
		SERVICE_NAME=$$s docker compose run --rm dev uv run python manage.py spectacular --file /app/$$s/openapi-schema.yaml;\
		SERVICE_NAME=$$s docker compose run --rm openapi-diff https://test.app.amsterdam.nl/$${SERVICE_NAME_HYPHEN}/api/v1/openapi/ /specs/openapi-schema.yaml --fail-on-incompatible || exit $$?; \
	  done; \
	else \
        SERVICE_NAME=$$SERVICE_NAME docker compose run --rm dev uv run python manage.py spectacular --file /app/$$SERVICE_NAME/openapi-schema.yaml;\
        SERVICE_NAME=$$SERVICE_NAME docker compose run --rm openapi-diff https://test.app.amsterdam.nl/$${SERVICE_NAME_HYPHEN}/api/v1/openapi/ /specs/openapi-schema.yaml --fail-on-incompatible || exit $$?; \
	fi

prepare-for-pr: requirements lintfix test openapi-diff
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

send_mijnamsterdam_notifications: check-service
	# Django command for the MijnAmsterdam service
	$(manage) sendmijnamsterdamnotifications

survey_mock_data: check-service
	# Load mock data for the survey service
	$(manage) surveymockdata

spectacular: check-service
    # Generate OpenAPI schema
	$(manage) spectacular --file /app/${SERVICE_NAME}/openapi-schema.yaml

migrations: check-service
    # Run Django migrations on database
	$(manage) makemigrations

migrate: check-service
    # Run Django migrations on database
    # Use the "TARGET_MIGRATION" (e.g. 0015) only for rolling back migrations
	$(manage) migrate $(TARGET_MIGRATION_APP) $(TARGET_MIGRATION)

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

superuser:
	# Create a superuser for the Django app
	$(manage) createsuperuser --username jeroen --email app@amsterdam.nl

