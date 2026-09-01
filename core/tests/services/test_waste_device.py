import datetime

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
        """Return all registered waste device ids."""
        self._create_device("device_1")
        self._create_device("device_2")
        device_1 = baker.make(WasteDevice, device_id="device_1")
        device_2 = baker.make(WasteDevice, device_id="device_2")

        result = self.service.get_device_ids()
        self.assertIn(device_1.device_id, result)
        self.assertIn(device_2.device_id, result)

    def test_bulk_create_waste_devices(self):
        """Create multiple waste-device rows in one bulk operation."""
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
        """Return only devices that are outdated and have a BAG id."""
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
        """Exclude outdated rows that do not have a BAG id."""
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
        """Update updated_at for the selected waste-device ids."""
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
        """Create missing Device records while preserving existing ones."""
        existing_device = self._create_device("existing_device")
        new_device_id = "new_device"

        self.service.ensure_devices_exist([existing_device.external_id, new_device_id])

        self.assertTrue(
            Device.objects.filter(external_id=existing_device.external_id).exists()
        )
        self.assertTrue(Device.objects.filter(external_id=new_device_id).exists())

    def test_get_device_ids_for_route_names_and_postal_area(self):
        """Filter devices by route name and postal area across route columns."""
        self._create_device("matching_device")
        self._create_device("wrong_postal_device")
        self._create_device("wrong_route_device")

        baker.make(
            WasteDevice,
            device_id="matching_device",
            route_name_organic="Route A",
            postal_area="1091",
        )
        baker.make(
            WasteDevice,
            device_id="wrong_postal_device",
            route_name_organic="Route A",
            postal_area="1011",
        )
        baker.make(
            WasteDevice,
            device_id="wrong_route_device",
            route_name_residual="Route B",
            postal_area="1091",
        )

        result = self.service.get_device_ids_for_route_names_and_postal_area(
            route_names=["Route A"],
            postal_area="1091",
        )

        self.assertEqual(result, ["matching_device"])

    def test_get_device_ids_for_route_names_and_postal_area_without_filters(self):
        """Return all device ids when no route-name or postal-area filters are provided."""
        self._create_device("device_no_filter_1")
        self._create_device("device_no_filter_2")
        baker.make(WasteDevice, device_id="device_no_filter_1")
        baker.make(WasteDevice, device_id="device_no_filter_2")

        result = self.service.get_device_ids_for_route_names_and_postal_area(
            route_names=None,
            postal_area=None,
        )

        self.assertCountEqual(result, ["device_no_filter_1", "device_no_filter_2"])

    def test_define_waste_device_instance(self):
        """Build a WasteDevice instance with the provided values."""
        updated_at = timezone.now()

        instance = self.service.define_waste_device_instance(
            device_id="device_instance",
            bag_nummeraanduiding_id="bag-1",
            updated_at=updated_at,
        )

        self.assertEqual(instance.device_id, "device_instance")
        self.assertEqual(instance.bag_nummeraanduiding_id, "bag-1")
        self.assertEqual(instance.updated_at, updated_at)

    def test_rows_helper_methods(self):
        """Return correct totals and latest route update timestamps from helper methods."""
        self._create_device("row_device_1")
        self._create_device("row_device_2")
        self._create_device("row_device_3")
        now = timezone.now()

        baker.make(
            WasteDevice,
            device_id="row_device_1",
            routes_updated_at=None,
        )
        baker.make(
            WasteDevice,
            device_id="row_device_2",
            routes_updated_at=now - datetime.timedelta(days=1),
        )
        baker.make(
            WasteDevice,
            device_id="row_device_3",
            routes_updated_at=now,
        )

        self.assertEqual(self.service.get_total_rows(), 3)
        self.assertEqual(self.service.get_rowcount_without_route_updated_at(), 1)
        self.assertEqual(self.service.get_rows_without_route_updated_at().count(), 1)
        self.assertEqual(self.service.get_latest_route_updated_at(), now)
