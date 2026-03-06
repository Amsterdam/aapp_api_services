# Copilot Instructions for Amsterdam App Backend

## Project Overview
- **Architecture:** Modular Django REST Framework backend. Each top-level directory (e.g., `bridge/`, `city_pass/`, `waste/`) is a Django app representing a distinct service or feature. Shared logic and settings are in `core/`.
- **Service Boundaries:** Each app is self-contained with its own models, serializers, views, URLs, and settings. Apps communicate via Django mechanisms (e.g., signals, shared models/utilities in `core/`).
- **Data Flow:** API requests are routed to the appropriate app via `ROOT_URLCONF` in each app's settings. Each app exposes its own OpenAPI docs at `/SERVICE_NAME/api/v1/apidocs`.

## Developer Workflows
- **Setup:**
  - Use Python 3.12.3, Docker, and [UV](https://astral.sh/uv/).
  - Create a venv and install dependencies with `uv pip install -r requirements.txt`.
- **Running Services:**
  - Only one service can run at a time (all use port 8000).
  - Start a service: `SERVICE_NAME=city_pass make dev` (replace `city_pass` as needed).
  - Run migrations: `SERVICE_NAME=city_pass make migrate`.
- **Testing:**
  - Run all tests: `make test` (ensure venv is active).
- **Pre-commit:**
  - Install hooks: `pip install pre-commit && pre-commit install`.

## Project Conventions
- **Settings Structure:** Each app has a `settings/` folder with `base.py`, `local.py`, and `otap.py`. Always import from `core.settings` as shown in the README.
- **Adding Apps:** Use `django-admin startapp`, then add a `settings/` structure and update `INSTALLED_APPS` and `ROOT_URLCONF`.
- **Dependencies:** Add new packages to `pyproject.toml` (not requirements.txt).
- **API Docs:** Each app exposes its own API docs endpoint.
- **External Integrations:**
  - Azure Application Insights for monitoring (see `core/` and app settings).
  - Google Firebase Messaging for notifications (see `notification/`).

## Key Files & Directories
- `core/`: Shared settings, middleware, authentication, and utilities.
- `Makefile`: Defines common dev/test commands.
- `requirements.txt` & `pyproject.toml`: Dependency management.
- `deploy/`: Deployment scripts.
- `.pre-commit-config.yaml`: Pre-commit hook config.

## Patterns & Examples
- **App Example:** See `city_pass/` for a full-featured app with authentication, serializers, and integration tests.
- **Settings Example:** See `city_pass/settings/base.py` for correct settings imports and structure.
- **Service Startup:** `SERVICE_NAME=city_pass make dev`
- **Testing:** `make test`

## Notes
- Do not run multiple services simultaneously (port conflict).
- Always activate the venv before running commands.
- Use the provided Makefile targets for all dev/test workflows.
- For new integrations, follow the patterns in `core/` and existing apps.
