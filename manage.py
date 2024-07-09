#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    is_testing = "test" in sys.argv

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main_application.settings_azure")

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
    print("API documentation: http://127.0.0.1:8000/city-pass/api/v1/apidocs")

    no_coverage = os.getenv("NO_COVERAGE", "false").lower() in ("true", "1")

    if is_testing is True and no_coverage is False:
        import coverage

        cov = coverage.coverage(
            source=["city_pass"],
            omit=["*/tests/*"],
            data_file="/app/tests/.coverage",
        )
        cov.erase()
        cov.start()

        execute_from_command_line(sys.argv)

        cov.stop()
        cov.save()
        cov.report()
    else:
        # Start the application
        execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
