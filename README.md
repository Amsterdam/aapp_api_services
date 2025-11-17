# Amsterdam App Backend

## About

This repository contains the backend files for the Amsterdam App. The Amsterdam App is a native app for citizens, entrepreneurs, and visitors of the City of Amsterdam to provide information, allow communication, and streamline transactions.

The backend is built using Django, and more specifically the REST framework of Django. Django allows us to have a modular approach, where each module is linked to a module in the application.

## Prerequisites

The following programs and tooling should be installed on your device:
- Python (3.12.3)
- UV
- Docker

Python and Docker can be installed via the K drive and UV can be installed as follows:
```curl -LsSf https://astral.sh/uv/install.sh | sh```

Besides that, it is necessary to install make and other build tools: `sudo apt install build-essential`

## Installation

The following steps should be followed to set up this project:

- Clone the repository: `git clone git@ssh.dev.azure.com:v3/CloudCompetenceCenter/Amsterdam-App/aapp_api_services`
- Switch to the repo directory: `cd aapp_api_services`
- Check your python version: `python3 --version`
- Install matching venv version: `sudo apt install python3.12-venv` (if your python version is 3.12)
- Install python3-dev: `sudo apt install python3-dev`
- Create a virtual environment: `python3 -m venv .venv`
- Activate the virtual environment: `./.venv/bin/activate`
- Install the dependencies inside the virtual environment: `uv pip install -r requirements.txt`

Run a service via this command:
`SERVICE_NAME=%service_name% make dev`, with `%service_name%` replaced by the name of the service you want to run, e.g. `bridge`, `city_pass`, `waste`, etc.

If there are necessary migrations, this will show in the logs when running the above command. To run the migrations: `SERVICE_NAME=%service_name% make migrate`

When running a service, the API docs can be found at: <http://127.0.0.1:8000/%service_name%/api/v1/apidocs>


## Initialize a new API app

Start a new app using this Django command:

    django-admin startapp our_new_app

Add settings file structure to new app:

    settings
    ├── __init__.py
    ├── base.py
    ├── local.py
    └── otap.py

`base.py` should contain at least:

    from core.settings.base import *  # isort:skip

    INSTALLED_APPS += [
        "our_new_app.apps.OurNewAppConfig",
    ]

    ROOT_URLCONF = "our_new_app.urls"

    SPECTACULAR_SETTINGS["TITLE"] = "New App API"

    LOGGING["loggers"]["our_new_app"] = {
        "level": "DEBUG",
        "handlers": ["console"],
        "propagate": False,
    }

`local.py` should contain at least:

    from .base import *  # isort:skip
    from core.settings.local import *  # isort:skip


`otap.py` should contain at least:

    from .base import *  # isort:skip
    from core.settings.otap import *  # isort:skip

    setup_opentelemetry(service_name="our-new-app")

## Project Structure

The project follows a modular structure, with each module representing a distinct feature or service. Below is an overview of key directories:

- `bridge/`: Contains core functionalities for bridging services.
- `city_pass/`: Manages city pass-related features.
- `construction_work/`: Handles construction work-related data and APIs.
- `contact/`: Manages contact-related features.
- `core/`: Includes shared utilities, settings, and middleware.
- `deploy/`: Contains a deployment script.
- `image/`: Process images in Azure Blob Storage.
- `modules/`: Handles top level data of the different modules.
- `notification/`: Handles notifications and related services.
- `survey/`: Manages survey-related functionalities.
- `waste/`: Handles waste management services.

Refer to the source code for detailed implementations within each module.

## Usage Instructions

Once the service is running (you can only run one service at a time as they use the same port), you can interact with the APIs via the API docs (<http://127.0.0.1:8000/%service_name%/api/v1/apidocs>) or using tools like Postman. Replace `%service_name%`  by the name of the service you have started, e.g. `bridge`, `city_pass`, `waste`, etc.

## Testing

To run tests, use the following command:

```bash
make test
```
This will execute all test cases across the project. Ensure that the virtual environment is activated before running tests.

## Troubleshooting

Here are some common issues and their solutions:

- **Dependency Conflicts**: Ensure that the virtual environment is activated and dependencies are installed using the correct `requirements.txt` file.
- **Migration Errors**: Run `make migrate` to apply any pending migrations.
- **Service Not Starting**: Check the logs for errors and ensure all environment variables are correctly set.


## External services

- **Azure Application Insights:** A comprehensive monitoring service that provides real-time error logging, performance tracking, and diagnostic insights to ensure the stability and reliability of our app.
- **Google Firebase Messaging:** Provides cloud messaging services to send push notifications and in-app messages, enabling real-time communication with users across platforms.


## Pre commit hooks
To use the pre-commit hooks as specified in `.pre-commit-config.yml`, first install `pre-commit` by running: `pip install pre-commit` (inside your virtual environment). Then run: `pre-commit install`.

If the `.pre-commit-config.yml` changes, you have to install the new pre-commit hooks. This will not update automatically.
