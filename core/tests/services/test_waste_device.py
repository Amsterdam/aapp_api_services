import datetime
from unittest.mock import patch

from django.utils import timezone
from model_bakery import baker

from core.services.waste_device import WasteDeviceService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models.notification_models import Device
from notification.models.waste_guide_models import WasteDevice


class TestWasteDeviceService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.service = WasteDeviceService()

    def _create_device(self, external_id):
        return baker.make(
            Device, external_id=external_id, os="ios", firebase_token=None
        )

    def test_get_device_ids(self):
        self._create_device("device_1")
        self._create_device("device_2")
        device_1 = baker.make(WasteDevice, device_id="device_1")
        device_2 = baker.make(WasteDevice, device_id="device_2")

        result = self.service.get_device_ids()
        self.assertIn(device_1.device_id, result)
        self.assertIn(device_2.device_id, result)

    def test_bulk_create_waste_devices(self):
        self._create_device("device_3")
        self._create_device("device_4")
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
        self._create_device("outdated_device")
        self._create_device("up_to_date_device")
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
        self._create_device("outdated_device")
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
        self._create_device("device_to_update")
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

    def test_ensure_devices_exist(self):
        existing_device = self._create_device("existing_device")
        new_device_id = "new_device"

        self.service.ensure_devices_exist([existing_device.external_id, new_device_id])

        self.assertTrue(
            Device.objects.filter(external_id=existing_device.external_id).exists()
        )
        self.assertTrue(Device.objects.filter(external_id=new_device_id).exists())

    def test_fill_empty_row_sets_routes_updated_at(self):
        self._create_device("device_with_route_data")
        waste_device = baker.make(
            WasteDevice,
            device_id="device_with_route_data",
            bag_nummeraanduiding_id="bag_123",
            routes_updated_at=None,
            route_name_organic=None,
            postal_area=None,
        )

        with patch.object(
            WasteDeviceService,
            "get_bag_nummeraanduiding_data",
            return_value=[
                {
                    "afvalwijzerFractieCode": "gft",
                    "afvalwijzerRoutenaam": "Route A",
                    "postcode": "1091AB",
                }
            ],
        ):
            result = self.service.fill_empty_row(waste_device)

        waste_device.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(waste_device.route_name_organic, "Route A")
        self.assertEqual(waste_device.postal_area, "1091")
        self.assertIsNotNone(waste_device.routes_updated_at)
