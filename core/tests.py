from django.conf import settings
from django.test import override_settings
from rest_framework.test import APITestCase


@override_settings(API_KEYS="test-api-key")
class BaseAPITestCase(APITestCase):
    def setUp(self) -> None:
        # Prepare API key for authentication
        api_keys = settings.API_KEYS.split(",")
        self.api_headers = {settings.API_KEY_HEADER: api_keys[0]}
