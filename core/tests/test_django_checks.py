import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_all_migrations():
    call_command("migrate")


def test_django_configuration_check():
    call_command("check")
