from model_bakery import baker

from bridge.mijnamsterdam.services.notifications import NotificationService
from core.enums import Module
from core.services.notification_service import NotificationData
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import Device, NotificationLast, ScheduledNotification


class TestNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.notification_service = NotificationService()
        self.device_id = "foobar"
        device = baker.make(Device, external_id=self.device_id)
        baker.make(
            NotificationLast,
            notification_scope=f"{Module.MIJN_AMS.value}:string",
            last_create="2025-07-27T10:07:38.603Z",
            device=device,
            module_slug=Module.MIJN_AMS.value,
        )
        baker.make(
            NotificationLast,
            notification_scope=f"{Module.MIJN_AMS.value}:string_2",
            last_create="2025-07-24T11:48:36.715Z",
            device=device,
            module_slug=Module.MIJN_AMS.value,
        )

    def test_send_notification(self):
        notification_data = NotificationData(
            link_source_id="foobar",
            title="Mijn Amsterdam melding",
            message="Er staat een nieuw bericht voor je klaar.",
            device_ids=["123", "456"],
            make_push=True,
        )
        self.notification_service.send(notification_data)
        self.assertEqual(ScheduledNotification.objects.count(), 1)
