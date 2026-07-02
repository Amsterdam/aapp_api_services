from django.urls import reverse

from core.tests.test_authentication import BasicAPITestCase
from news.models.article_models import NewsArticle


class TestDistrictListView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("news-districts-list")

    def test_get_districts(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.data["data"]),
            len(NewsArticle._meta.get_field("district").choices),
        )
        self.assertIn(
            {"label": "noord", "name": "Stadsdeel Noord"}, response.data["data"]
        )
        self.assertIn(
            {"label": "weesp", "name": "Stadsgebied Weesp"}, response.data["data"]
        )
