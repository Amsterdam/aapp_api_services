import datetime

from django.utils import timezone
from model_bakery import baker

from core.services.waste_device import WasteDeviceService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import WasteDevice


class TestWasteDeviceService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.service = WasteDeviceService()

    def test_get_device_ids(self):
        device_1 = baker.make(WasteDevice, device_id="device_1")
        device_2 = baker.make(WasteDevice, device_id="device_2")

        result = self.service.get_device_ids()
        self.assertIn(device_1.device_id, result)
        self.assertIn(device_2.device_id, result)

    def test_bulk_create_waste_devices(self):
        waste_device_1 = self.service.define_waste_device_instance(
            device_id="device_3",
            bag_nummeraanduiding_id="123",
            updated_at=timezone.now(),
        )
        waste_device_2 = self.service.define_waste_device_instance(
            device_id="device_4",
            bag_nummeraanduiding_id="456",
            updated_at=timezone.now(),
        )

        self.service.bulk_create_waste_devices([waste_device_1, waste_device_2])

        self.assertTrue(WasteDevice.objects.filter(device_id="device_3").exists())
        self.assertTrue(WasteDevice.objects.filter(device_id="device_4").exists())

    def test_get_outdated_waste_devices(self):
        outdated_device = baker.make(
            WasteDevice,
            device_id="outdated_device",
            bag_nummeraanduiding_id="789",
            updated_at=datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(days=1),
                datetime.time(hour=0, minute=0),
            ),
        )
        up_to_date_device = baker.make(
            WasteDevice,
            device_id="up_to_date_device",
            bag_nummeraanduiding_id="101",
            updated_at=timezone.now(),
        )

        result = self.service.get_outdated_waste_devices()
        self.assertIn(outdated_device, result)
        self.assertNotIn(up_to_date_device, result)

    def test_get_outdated_no_id_waste_devices(self):
        outdated_device = baker.make(
            WasteDevice,
            device_id="outdated_device",
            bag_nummeraanduiding_id=None,
            updated_at=datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(days=1),
                datetime.time(hour=0, minute=0),
            ),
        )

        result = self.service.get_outdated_waste_devices()
        self.assertNotIn(outdated_device, result)

    def test_update_waste_device(self):
        device = baker.make(
            WasteDevice,
            device_id="device_to_update",
            updated_at=datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(days=1),
                datetime.time(hour=0, minute=0),
            ),
        )

        self.service.update_waste_device(ids_to_update=[device.device_id])
        device.refresh_from_db()
        self.assertTrue(
            device.updated_at > timezone.now() - datetime.timedelta(minutes=1)
        )
