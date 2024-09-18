from django.urls import reverse
from rest_framework import status

from core.tests import BaseAPITestCase


class TestLinkView(BaseAPITestCase):
    def test_load_data_get_data(self):
        url = reverse("contact-links")
        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
