from django.urls import reverse

from core.tests.test_authentication import BasicAPITestCase
from news.models import NewsArticle


class TestDistrictListView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("news-districts-list")

    def test_get_districts(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        expected_data = [
            {"label": district[0], "name": district[1]}
            for district in NewsArticle._meta.get_field("district").choices
        ]
        self.assertEqual(response.data["data"], expected_data)
