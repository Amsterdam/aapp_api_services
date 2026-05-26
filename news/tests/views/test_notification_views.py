from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import BasicAPITestCase
from news.models import LiveblogNotification, NewsArticle


class TestNotificationView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("news-notification")
        self.device_id = "foobar"
        self.api_headers["DeviceId"] = self.device_id

    def test_get_notification_empty(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)

    def test_get_notification(self):
        article = baker.make(NewsArticle, type="article")
        baker.make(LiveblogNotification, device_id=self.device_id, article=article)

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device_id"], self.device_id)

    def test_post_notification(self):
        article = baker.make(NewsArticle, type="article", foreign_id="123")

        response = self.client.post(
            self.url,
            data={"article_foreign_id": article.foreign_id},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LiveblogNotification.objects.first().device_id, self.device_id)

    def test_delete_notification(self):
        article = baker.make(NewsArticle, type="article")
        baker.make(LiveblogNotification, device_id=self.device_id, article=article)

        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)

    def test_delete_notification_empty(self):
        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
