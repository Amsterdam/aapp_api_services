from datetime import datetime

from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import BasicAPITestCase
from news.models import NewsArticle, NewsArticleImage


class TestArticleListView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("news-article-list")
        self.article_1 = baker.make(
            NewsArticle,
            publication_date=datetime(2024, 10, 11, 12, 30, 10).isoformat(),
            type="article",
        )
        self.article_2 = baker.make(
            NewsArticle,
            publication_date=datetime(2024, 10, 12, 14, 45, 15).isoformat(),
            type="article",
        )
        self.article_3 = baker.make(
            NewsArticle,
            publication_date=datetime(2024, 10, 12, 14, 45, 15).isoformat(),
            type="highlight",
        )
        self.article_4 = baker.make(
            NewsArticle,
            publication_date=datetime(2024, 10, 12, 14, 45, 15).isoformat(),
            type="district",
            district="noord",
        )
        self.article_1_image_1 = baker.make(NewsArticleImage, article=self.article_1)
        self.article_1_image_2 = baker.make(NewsArticleImage, article=self.article_1)

    def test_article_list(self):
        response = self.client.get(
            self.url, data={"type", "article"}, headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        article_1_response = [
            article for article in response.data if article["id"] == self.article_1.id
        ][0]
        self.assertEqual(article_1_response["title"], self.article_1.title)
        self.assertEqual(
            article_1_response["publication_date"], "2024-10-11T12:30:10+02:00"
        )
        self.assertEqual(len(article_1_response["images"]), 2)

        article_2_response = [
            article for article in response.data if article["id"] == self.article_2.id
        ][0]
        self.assertEqual(article_2_response["title"], self.article_2.title)
        self.assertEqual(
            article_2_response["publication_date"], "2024-10-12T14:45:15+02:00"
        )
        self.assertEqual(len(article_2_response["images"]), 0)

    def test_highlight_list(self):
        response = self.client.get(
            self.url, data={"type", "highlight"}, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_liveblog_list(self):
        response = self.client.get(
            self.url, data={"type", "liveblog"}, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_foobar_list(self):
        response = self.client.get(
            self.url, data={"type", "foobar"}, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)

    def test_district_list(self):
        response = self.client.get(
            self.url,
            data={"type": "district", "district": "noord"},
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_district_list_empty(self):
        response = self.client.get(
            self.url,
            data={"type": "district", "district": "zuid"},
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_district_list_invalid(self):
        response = self.client.get(
            self.url,
            data={"type": "district", "district": "foobar"},
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_district_list_without_district(self):
        response = self.client.get(
            self.url, data={"type": "district"}, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)


class TestArticleDetailView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        article_id = 123
        self.url = reverse("news-article-detail", kwargs={"id": article_id})
        self.article_1 = baker.make(
            NewsArticle,
            id=article_id,
            type="article",
            publication_date=datetime(2024, 10, 11, 12, 30, 10).isoformat(),
        )
        self.article_2 = baker.make(
            NewsArticle,
            type="article",
            publication_date=datetime(2024, 10, 12, 14, 45, 15).isoformat(),
        )
        self.article_1_image_1 = baker.make(NewsArticleImage, article=self.article_1)
        self.article_1_image_2 = baker.make(NewsArticleImage, article=self.article_1)

    def test_article_detail(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["title"], self.article_1.title)
        self.assertEqual(response.data["publication_date"], "2024-10-11T12:30:10+02:00")
        self.assertEqual(len(response.data["images"]), 2)

    def test_article_id_not_found(self):
        url = reverse("news-article-detail", kwargs={"id": 999})
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)
