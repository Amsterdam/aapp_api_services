import json

import freezegun
import responses
from django.conf import settings
from django.contrib.auth.models import User

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.models import ManualNotification, NotificationSchedule
from waste.services.notification import ManualNotificationService, NotificationService


@freezegun.freeze_time("2021-08-01")
class NotificationServiceTest(ResponsesActivatedAPITestCase):
    def test_call_notification_service(self):
        resp_post = responses.post(
            settings.NOTIFICATION_ENDPOINTS["SCHEDULED_NOTIFICATION"],
            json={"status": "success"},
        )

        notification_service = NotificationService()
        notification_service.send_waste_notification(
            device_ids=["device1", "device2"],
            waste_type="glas",
        )

        self.assertEqual(resp_post.call_count, 1)

        call = responses.calls[0].request
        json_body = json.loads(call.body)
        self.assertEqual(json_body["title"], "Afvalwijzer")
        self.assertIn("Morgen halen we glas in uw buurt op.", json_body["body"])
        self.assertEqual(json_body["module_slug"], "waste-guide")
        self.assertEqual(json_body["notification_type"], "waste-guide:date-reminder")
        self.assertEqual(json_body["device_ids"], ["device1", "device2"])


class ManualNotificationServiceTest(ResponsesActivatedAPITestCase):
    def test_call_notification_service(self):
        resp_post = responses.post(
            settings.NOTIFICATION_ENDPOINTS["SCHEDULED_NOTIFICATION"],
            json={"status": "success"},
        )
        for device in ["device1", "device2", "device3"]:
            NotificationSchedule.objects.create(
                device_id=device, bag_nummeraanduiding_id="foobar"
            )

        notification_service = ManualNotificationService()
        notification = ManualNotification.objects.create(
            title="Vanaf morgen kun je de kerstbook aan de straat zetten",
            message="Zorg dat je hem op de goede plek zet",
            created_by=User.objects.create_user(
                username="testuser", password="testpass"
            ),
        )
        notification_service.send(notification=notification)

        self.assertEqual(resp_post.call_count, 1)

        call = responses.calls[0].request
        json_body = json.loads(call.body)
        self.assertEqual(
            json_body["title"], "Vanaf morgen kun je de kerstbook aan de straat zetten"
        )
        self.assertEqual(json_body["body"], "Zorg dat je hem op de goede plek zet")
        self.assertEqual(json_body["module_slug"], "waste-guide")
        self.assertEqual(
            json_body["notification_type"], "waste-guide:manual-notification"
        )
        self.assertEqual(json_body["device_ids"], ["device1", "device2", "device3"])
