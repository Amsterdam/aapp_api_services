import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status


class TestCityOfficeView(TestCase):
    @override_settings(
        CSV_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv"),
        API_KEYS="amsterdam",
    )
    def test_load_data_get_data(self):
        call_command("loaddata")

        url = reverse("contact-city-offices")
        api_keys = settings.API_KEYS.split(",")
        headers = {settings.API_KEY_HEADER: api_keys[0]}
        response = self.client.get(url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
