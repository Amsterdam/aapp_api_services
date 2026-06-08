from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import BasicAPITestCase
from news.models import LiveblogNotification, NewsArticle


class TestNotificationView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("news-notification", kwargs={"article_id": 1})
        self.device_id = "foobar"
        self.api_headers["DeviceId"] = self.device_id

    def test_get_notification_empty(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)

    def test_get_notification(self):
        article = baker.make(NewsArticle, id=1, is_liveblog=True)
        baker.make(LiveblogNotification, device_id=self.device_id, article=article)

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device_id"], self.device_id)

    def test_post_notification(self):
        baker.make(NewsArticle, id=1, is_liveblog=True)
        response = self.client.post(
            self.url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(LiveblogNotification.objects.first().device_id, self.device_id)

    def test_post_notification_with_liveblog_flag_and_non_liveblog_type(self):
        baker.make(NewsArticle, id=1, in_all_news=True, is_liveblog=True)
        response = self.client.post(
            self.url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 201)

    def test_post_notification_not_liveblog(self):
        baker.make(NewsArticle, id=1, in_all_news=True)
        response = self.client.post(
            self.url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 400)

    def test_post_notification_deleted_liveblog(self):
        baker.make(NewsArticle, id=1, is_liveblog=True, deleted=True)
        response = self.client.post(
            self.url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(LiveblogNotification.objects.count(), 0)

    def test_post_notification_already_exists(self):
        article = baker.make(NewsArticle, id=1, is_liveblog=True)
        baker.make(LiveblogNotification, device_id=self.device_id, article=article)

        response = self.client.post(
            self.url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LiveblogNotification.objects.first().device_id, self.device_id)

    def test_delete_notification(self):
        article = baker.make(NewsArticle, in_all_news=True)
        baker.make(LiveblogNotification, device_id=self.device_id, article=article)

        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)

    def test_delete_notification_empty(self):
        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
