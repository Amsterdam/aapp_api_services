import json

import freezegun
import responses
from django.conf import settings

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.services.notification import NotificationService


@freezegun.freeze_time("2021-08-01")
class NotificationServiceTest(ResponsesActivatedAPITestCase):
    def test_call_notification_service(self):
        resp_post = responses.post(
            settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"],
            json={"status": "success"},
        )

        notification_service = NotificationService()
        notification_service.send(device_ids=["device1", "device2"], type="glas")

        self.assertEqual(resp_post.call_count, 1)

        call = responses.calls[0].request
        json_body = {
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
            "make_push": True,
        }
        self.assertEqual(json.loads(call.body), json_body)
