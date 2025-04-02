from unittest.mock import patch

import freezegun
from django.test import TestCase

from waste.services.notification import call_notification_service, get_request_data


@freezegun.freeze_time("2021-08-01")
class NotificationServiceTest(TestCase):
    def test_get_request_data(self):
        request_data = get_request_data(["device1", "device2"], "glas")
        self.assertEqual(request_data["module_slug"], "waste")
        self.assertEqual(request_data["device_ids"], ["device1", "device2"])
        self.assertEqual(request_data["title"], "Morgen wordt je glas afval opgehaald")
        self.assertEqual(request_data["created_at"], "2021-08-01T00:00:00+00:00")

    @patch("waste.services.notification.requests.post")
    def test_call_notification_service(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}
        response = call_notification_service(["device1", "device2"], "glas")

        self.assertEqual(response, (200, {"status": "success"}))
        mock_post.assert_called_once()
        mock_post.assert_called_with(
            "http://api-notification:8000/internal/api/v1/notification",
            json={
                "title": "Morgen wordt je glas afval opgehaald",
                "body": "Denk er aan om je container buiten te zetten",
                "module_slug": "waste",
                "context": {
                    "linkSourceid": "glas",
                    "type": "WasteDateReminder",
                    "module_slug": "waste",
                },
                "created_at": "2021-08-01T00:00:00+00:00",
                "device_ids": ["device1", "device2"],
                "notification_type": "waste:date-reminder",
            },
        )
