import freezegun
from django.contrib.auth.models import User

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import ScheduledNotification
from waste.models import ManualNotification, NotificationSchedule
from waste.services.notification import ManualNotificationService, NotificationService


@freezegun.freeze_time("2021-08-01")
class NotificationServiceTest(ResponsesActivatedAPITestCase):
    def test_call_notification_service(self):
        notification_service = NotificationService()
        notification_service.send_waste_notification(
            device_ids=["device1", "device2"],
            waste_type="glas",
        )

        notification = ScheduledNotification.objects.first()
        self.assertEqual(notification.title, "Afvalwijzer")
        self.assertIn("Morgen halen we glas in uw buurt op.", notification.body)
        self.assertEqual(notification.module_slug, "waste-guide")
        self.assertEqual(notification.notification_type, "waste-guide:date-reminder")
        devices = set(notification.devices.values_list("external_id", flat=True))
        self.assertEqual(devices, {"device1", "device2"})


class ManualNotificationServiceTest(ResponsesActivatedAPITestCase):
    def test_call_notification_service(self):
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

        notification = ScheduledNotification.objects.first()
        self.assertEqual(
            notification.title, "Vanaf morgen kun je de kerstbook aan de straat zetten"
        )
        self.assertEqual(notification.body, "Zorg dat je hem op de goede plek zet")
        self.assertEqual(notification.module_slug, "waste-guide")
        self.assertEqual(
            notification.notification_type, "waste-guide:manual-notification"
        )
        devices = set(notification.devices.values_list("external_id", flat=True))
        self.assertEqual(devices, {"device1", "device2", "device3"})
