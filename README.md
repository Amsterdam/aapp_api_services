# How To

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
