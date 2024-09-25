#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.base")

    # Always read environment variables via manage.py
    load_dotenv()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Give developer easy access to API docs
    print("API documentation: http://127.0.0.1:8000/<service_name>/api/v1/apidocs")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
