import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_all_migrations():
    call_command("migrate", "--check")


@pytest.mark.django_db
def test_missing_migrations():
    call_command("makemigrations", "--check")


def test_django_configuration_check():
    call_command("check")
