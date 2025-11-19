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
            settings.NOTIFICATION_ENDPOINTS["SCHEDULED_NOTIFICATION"],
            json={"status": "success"},
        )

        notification_service = NotificationService()
        notification_service.send(device_ids=["device1", "device2"], type="glas")

        self.assertEqual(resp_post.call_count, 1)

        call = responses.calls[0].request
        json_body = json.loads(call.body)
        self.assertEqual(json_body["title"], "Morgen wordt je glas afval opgehaald")
        self.assertEqual(
            json_body["body"], "Denk er aan om je container buiten te zetten"
        )
        self.assertEqual(json_body["module_slug"], "waste")
        self.assertEqual(json_body["notification_type"], "waste:date-reminder")
        self.assertEqual(json_body["device_ids"], ["device1", "device2"])
