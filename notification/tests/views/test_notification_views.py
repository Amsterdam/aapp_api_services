from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from core.tests.test_authentication import BasicAPITestCase
from notification.models import Client, Notification


class NotificationBaseTests(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client_id = "123"
        self.headers_with_client_id = {"ClientId": self.client_id, **self.api_headers}


class NotificationListViewTests(NotificationBaseTests):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-list-notifications")

    def test_list_notifications(self):
        client_1 = baker.make(Client, external_id=self.client_id)
        baker.make(Notification, client=client_1)
        baker.make(Notification, client=baker.make(Client))

        response = self.client.get(self.url, headers=self.headers_with_client_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 1
        )  # Only notifications for client_id "123" should be returned
        self.assertIn("title", response.data[0])
        self.assertIn("body", response.data[0])
        self.assertIn("module_slug", response.data[0])

    def test_list_notifications_missing_client_id(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: ClientId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotificationReadViewTests(NotificationBaseTests):
    def setUp(self):
        super().setUp()
        self.test_client = baker.make(Client, external_id=self.client_id)
        self.url = reverse("notification-read-notifications")

    def test_mark_all_as_read(self):
        notification = baker.make(Notification, client=self.test_client, is_read=False)

        response = self.client.post(self.url, headers=self.headers_with_client_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIn("1 notifications marked as read.", response.data["detail"])

    def test_mark_all_as_read_5(self):
        [
            baker.make(Notification, client=self.test_client, is_read=False)
            for _ in range(5)
        ]

        response = self.client.post(self.url, headers=self.headers_with_client_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("5 notifications marked as read.", response.data["detail"])

    def test_mark_unread_as_read(self):
        [
            baker.make(Notification, client=self.test_client, is_read=False)
            for _ in range(4)
        ]
        [
            baker.make(Notification, client=self.test_client, is_read=True)
            for _ in range(3)
        ]

        response = self.client.post(self.url, headers=self.headers_with_client_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("4 notifications marked as read.", response.data["detail"])

    def test_mark_only_client_as_read(self):
        [
            baker.make(Notification, client=self.test_client, is_read=False)
            for _ in range(2)
        ]
        [
            baker.make(Notification, client=baker.make(Client), is_read=False)
            for _ in range(8)
        ]

        response = self.client.post(self.url, headers=self.headers_with_client_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("2 notifications marked as read.", response.data["detail"])

    def test_mark_all_as_read_missing_client_id(self):
        response = self.client.post(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: ClientId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotificationDetailViewTests(NotificationBaseTests):
    def setUp(self):
        super().setUp()
        self.notification = baker.make(
            Notification, client=baker.make(Client, external_id="123"), is_read=False
        )
        self.url = reverse(
            "notification-detail-notification",
            kwargs={"notification_id": self.notification.id},
        )

    def test_get_notification_detail(self):
        response = self.client.get(self.url, headers=self.headers_with_client_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.notification.id))
        self.assertIn("title", response.data)
        self.assertIn("body", response.data)
        self.assertIn("module_slug", response.data)

    def test_update_notification_status(self):
        response = self.client.patch(
            self.url,
            data={"is_read": True},
            format="json",
            headers=self.headers_with_client_id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_get_notification_status_wrong_client_id(self):
        headers = {"ClientId": "Foobar", **self.api_headers}
        response = self.client.get(self.url, headers=headers)
        self.assertContains(
            response,
            "No Notification matches the given query.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_update_notification_status_wrong_client_id(self):
        headers = {"ClientId": "Foobar", **self.api_headers}
        response = self.client.patch(
            self.url, data={"is_read": True}, format="json", headers=headers
        )
        self.assertContains(
            response,
            "No Notification matches the given query.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_update_notification_title(self):
        old_title = self.notification.title
        response = self.client.patch(
            self.url,
            data={"is_read": False, "title": "foobar"},
            format="json",
            headers=self.headers_with_client_id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertEqual(
            self.notification.title, old_title
        )  # Title should not be updated
        self.assertFalse(self.notification.is_read)

    def test_get_notification_detail_missing_client_id(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: ClientId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_update_notification_detail_missing_client_id(self):
        response = self.client.patch(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: ClientId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
