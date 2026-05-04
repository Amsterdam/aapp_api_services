import datetime

import freezegun
from django.utils import timezone
from model_bakery import baker

from core.services.burning_guide_device import BurningGuideDeviceService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import BurningGuideDevice


class TestBurningGuideDeviceService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.service = BurningGuideDeviceService()

    def test_get_device_ids(self):
        device_1 = baker.make(BurningGuideDevice, device_id="device_1")
        device_2 = baker.make(BurningGuideDevice, device_id="device_2")

        result = self.service.get_device_ids()
        self.assertIn(device_1.device_id, result)
        self.assertIn(device_2.device_id, result)

    def test_bulk_create_burning_guide_devices(self):
        burning_guide_device_1 = self.service.define_burning_guide_device_instance(
            device_id="device_3",
            postal_code="123",
            send_at=timezone.now(),
        )
        burning_guide_device_2 = self.service.define_burning_guide_device_instance(
            device_id="device_4",
            postal_code="456",
            send_at=timezone.now(),
        )

        self.service.bulk_create_burning_guide_devices(
            [burning_guide_device_1, burning_guide_device_2]
        )

        self.assertTrue(
            BurningGuideDevice.objects.filter(device_id="device_3").exists()
        )
        self.assertTrue(
            BurningGuideDevice.objects.filter(device_id="device_4").exists()
        )

    @freezegun.freeze_time("2026-06-15 09:59:30")
    def test_get_outdated_burning_guide_devices(self):
        outdated_device = baker.make(
            BurningGuideDevice,
            device_id="outdated_device",
            postal_code="789",
            send_at=datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(days=1),
                datetime.time(hour=0, minute=0),
            ),
        )
        up_to_date_device = baker.make(
            BurningGuideDevice,
            device_id="up_to_date_device",
            postal_code="101",
            send_at=timezone.now(),
        )

        last_timestamp = datetime.datetime(2026, 6, 15, 7, 0, 0)

        result = self.service.get_outdated_burning_guide_devices(last_timestamp)
        self.assertIn(outdated_device, result)
        self.assertNotIn(up_to_date_device, result)

    @freezegun.freeze_time("2026-06-15 09:59:30")
    def test_get_outdated_no_postal_code_burning_guide_devices(self):
        outdated_device = baker.make(
            BurningGuideDevice,
            device_id="outdated_device",
            postal_code=None,
            send_at=datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(days=1),
                datetime.time(hour=0, minute=0),
            ),
        )

        last_timestamp = datetime.datetime(2026, 6, 15, 7, 0, 0)
        result = self.service.get_outdated_burning_guide_devices(last_timestamp)
        self.assertNotIn(outdated_device, result)

    def test_update_burning_guide_device(self):
        device = baker.make(
            BurningGuideDevice,
            device_id="device_to_update",
            send_at=datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(days=1),
                datetime.time(hour=0, minute=0),
            ),
        )

        self.service.update_burning_guide_devices(device_ids=[device.device_id])
        device.refresh_from_db()
        self.assertTrue(device.send_at > timezone.now() - datetime.timedelta(minutes=1))
