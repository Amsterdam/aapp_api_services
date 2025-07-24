from unittest.mock import patch

import freezegun
from django.test import TestCase

from waste.services.notification import NotificationService


@freezegun.freeze_time("2021-08-01")
class NotificationServiceTest(TestCase):
    @patch("core.services.notification.requests.post")
    def test_call_notification_service(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}

        notification_service = NotificationService()
        notification_service.send(device_ids=["device1", "device2"], type="glas")

        mock_post.assert_called_once()
        mock_post.assert_called_with(
            "http://api-notification:8000/internal/api/v1/notification",
            json={
                "title": "Morgen wordt je glas afval opgehaald",
                "body": "Denk er aan om je container buiten te zetten",
                "module_slug": "waste",
                "notification_type": "waste:date-reminder",
                "created_at": "2021-08-01T00:00:00+00:00",
                "context": {
                    "linkSourceid": "glas",
                    "type": "waste:date-reminder",
                    "module_slug": "waste",
                },
                "device_ids": ["device1", "device2"],
            },
            headers={"X-Api-Key": "insecure1"},
        )
