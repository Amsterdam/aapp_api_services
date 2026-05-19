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
            publication_datetime=datetime(2024, 10, 11, 12, 30, 10).isoformat(),
        )
        self.article_2 = baker.make(
            NewsArticle,
            publication_datetime=datetime(2024, 10, 12, 14, 45, 15).isoformat(),
        )
        self.article_1_image_1 = baker.make(NewsArticleImage, article=self.article_1)
        self.article_1_image_2 = baker.make(NewsArticleImage, article=self.article_1)

    def test_article_list(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["count"], 2)

        article_1_response = [
            article
            for article in response.data["results"]
            if article["id"] == self.article_1.id
        ][0]
        self.assertEqual(article_1_response["title"], self.article_1.title)
        self.assertEqual(
            article_1_response["publication_datetime"], "2024-10-11T12:30:10+02:00"
        )
        self.assertEqual(len(article_1_response["images"]), 2)

        article_2_response = [
            article
            for article in response.data["results"]
            if article["id"] == self.article_2.id
        ][0]
        self.assertEqual(article_2_response["title"], self.article_2.title)
        self.assertEqual(
            article_2_response["publication_datetime"], "2024-10-12T14:45:15+02:00"
        )
        self.assertEqual(len(article_2_response["images"]), 0)

    def test_article_list_pagination(self):
        params = {"page_size": 1}
        response = self.client.get(self.url, headers=self.api_headers, data=params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)  # Page size set to 1
        self.assertEqual(response.data["count"], 2)  # Total articles


class TestArticleDetailView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        article_id = 123
        self.url = reverse("news-article-detail", kwargs={"id": article_id})
        self.article_1 = baker.make(
            NewsArticle,
            id=article_id,
            publication_datetime=datetime(2024, 10, 11, 12, 30, 10).isoformat(),
        )
        self.article_2 = baker.make(
            NewsArticle,
            publication_datetime=datetime(2024, 10, 12, 14, 45, 15).isoformat(),
        )
        self.article_1_image_1 = baker.make(NewsArticleImage, article=self.article_1)
        self.article_1_image_2 = baker.make(NewsArticleImage, article=self.article_1)

    def test_article_detail(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["title"], self.article_1.title)
        self.assertEqual(
            response.data["publication_datetime"], "2024-10-11T12:30:10+02:00"
        )
        self.assertEqual(len(response.data["images"]), 2)

    def test_article_id_not_found(self):
        url = reverse("news-article-detail", kwargs={"id": 999})
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)
