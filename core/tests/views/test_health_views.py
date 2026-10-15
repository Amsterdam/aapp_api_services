from django.urls import reverse

from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestHealthCheckView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("health-check")

    def test_health_check(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
