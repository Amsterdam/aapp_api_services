from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from core.exceptions import MissingDeviceIdHeader
from core.tests.test_authentication import BasicAPITestCase
from news.models.article_models import LiveblogNotification, NewsArticle


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

    def test_post_notification_with_multiple_flags(self):
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


class TestDeleteDeviceDataView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("news-device-delete")
        self.device_id = "foobar"
        self.api_headers[settings.HEADER_DEVICE_ID] = self.device_id

    def test_delete_device_data(self):
        article_1 = baker.make(NewsArticle)
        article_2 = baker.make(NewsArticle)
        baker.make(LiveblogNotification, device_id=self.device_id, article=article_1)
        baker.make(LiveblogNotification, device_id=self.device_id, article=article_2)
        baker.make(LiveblogNotification, device_id="another-device", article=article_1)

        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            LiveblogNotification.objects.filter(device_id=self.device_id).count(),
            0,
        )
        self.assertEqual(LiveblogNotification.objects.count(), 1)

    def test_delete_device_data_unknown_device(self):
        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_device_data_idempotent(self):
        article = baker.make(NewsArticle)
        baker.make(LiveblogNotification, device_id=self.device_id, article=article)

        first_response = self.client.delete(self.url, headers=self.api_headers)
        second_response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(first_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(second_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_device_data_missing_device_id(self):
        headers = {
            key: value
            for key, value in self.api_headers.items()
            if key != settings.HEADER_DEVICE_ID
        }

        response = self.client.delete(self.url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_delete_device_data_missing_api_key(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
