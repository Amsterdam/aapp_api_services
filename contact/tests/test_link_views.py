from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status


class TestLinkView(TestCase):
    @override_settings(API_KEYS="amsterdam")
    def test_load_data_get_data(self):
        url = reverse("contact-links")
        api_keys = settings.API_KEYS.split(",")
        headers = {settings.API_KEY_HEADER: api_keys[0]}
        response = self.client.get(url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
