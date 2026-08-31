import datetime
from unittest.mock import Mock, patch

import requests
from django.test import override_settings
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

    def test_fill_empty_row_sets_routes_updated_at(self):
        """Populate route fields, postal area and routes_updated_at from API data."""
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

    def test_process_batch_counts_updated_skipped_and_has_more(self):
        """Track updated and skipped rows and return pagination metadata for a batch."""
        self._create_device("batch_a")
        self._create_device("batch_b")
        self._create_device("batch_c")
        baker.make(WasteDevice, device_id="batch_a")
        baker.make(WasteDevice, device_id="batch_b")
        baker.make(WasteDevice, device_id="batch_c")

        with patch.object(
            WasteDeviceService,
            "fill_empty_row",
            side_effect=[True, False],
        ):
            result = self.service.process_batch(batch_size=2)

        self.assertEqual(result["processed"], 2)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["last_pk"], "batch_b")
        self.assertTrue(result["has_more"])

    def test_process_batch_counts_failed_rows(self):
        """Count rows as failed when fill_empty_row raises an unexpected exception."""
        self._create_device("batch_failing")
        baker.make(WasteDevice, device_id="batch_failing")

        with patch.object(
            WasteDeviceService,
            "fill_empty_row",
            side_effect=Exception("boom"),
        ):
            result = self.service.process_batch(batch_size=1)

        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["last_pk"], "batch_failing")
        self.assertTrue(result["has_more"])

    def test_process_batch_returns_empty_result_when_no_rows(self):
        """Return an empty-batch response when there are no rows to process."""
        result = self.service.process_batch(batch_size=5, last_pk="non_existing")

        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["last_pk"], "non_existing")
        self.assertFalse(result["has_more"])

    def test_fill_empty_row_without_bag_id(self):
        """Skip row update when bag_nummeraanduiding_id is missing."""
        self._create_device("missing_bag_device")
        waste_device = baker.make(
            WasteDevice,
            device_id="missing_bag_device",
            bag_nummeraanduiding_id=None,
            routes_updated_at=None,
        )

        result = self.service.fill_empty_row(waste_device)

        waste_device.refresh_from_db()
        self.assertFalse(result)
        self.assertIsNone(waste_device.routes_updated_at)

    def test_fill_empty_row_without_api_data(self):
        """Skip row update when afvalwijzer API returns no rows."""
        self._create_device("no_data_device")
        waste_device = baker.make(
            WasteDevice,
            device_id="no_data_device",
            bag_nummeraanduiding_id="bag_456",
            routes_updated_at=None,
        )

        with patch.object(
            WasteDeviceService,
            "get_bag_nummeraanduiding_data",
            return_value=[],
        ):
            result = self.service.fill_empty_row(waste_device)

        waste_device.refresh_from_db()
        self.assertFalse(result)
        self.assertIsNone(waste_device.routes_updated_at)

    def test_fill_empty_row_without_matching_fraction_or_postcode(self):
        """Skip row update when response contains no known fraction and no postcode."""
        self._create_device("unknown_fraction_device")
        waste_device = baker.make(
            WasteDevice,
            device_id="unknown_fraction_device",
            bag_nummeraanduiding_id="bag_789",
            routes_updated_at=None,
        )

        with patch.object(
            WasteDeviceService,
            "get_bag_nummeraanduiding_data",
            return_value=[
                {
                    "afvalwijzerFractieCode": "unknown",
                    "afvalwijzerRoutenaam": "Route X",
                    "postcode": None,
                }
            ],
        ):
            result = self.service.fill_empty_row(waste_device)

        waste_device.refresh_from_db()
        self.assertFalse(result)
        self.assertIsNone(waste_device.routes_updated_at)

    @override_settings(
        WASTE_GUIDE_URL="https://waste.example/api",
        WASTE_GUIDE_API_KEY="test-key",
        ENVIRONMENT_SLUG="a",
    )
    def test_get_bag_nummeraanduiding_data_with_api_key_header(self):
        """Send X-Api-Key header in accepted environments and parse afvalwijzer rows."""
        with patch.object(
            WasteDeviceService,
            "make_get_request",
            return_value={"_embedded": {"afvalwijzer": [{"test": 1}]}},
        ) as mocked_request:
            result = self.service.get_bag_nummeraanduiding_data("bag_123")

        self.assertEqual(result, [{"test": 1}])
        mocked_request.assert_called_once_with(
            url="https://waste.example/api",
            headers={"X-Api-Key": "test-key"},
            params={"bagNummeraanduidingId": "bag_123"},
        )

    @override_settings(
        WASTE_GUIDE_URL="https://waste.example/api",
        WASTE_GUIDE_API_KEY="test-key",
        ENVIRONMENT_SLUG="t",
    )
    def test_get_bag_nummeraanduiding_data_without_api_key_header(self):
        """Skip X-Api-Key header outside accepted environments."""
        with patch.object(
            WasteDeviceService,
            "make_get_request",
            return_value={"_embedded": {"afvalwijzer": []}},
        ) as mocked_request:
            self.service.get_bag_nummeraanduiding_data("bag_123")

        mocked_request.assert_called_once_with(
            url="https://waste.example/api",
            headers=None,
            params={"bagNummeraanduidingId": "bag_123"},
        )

    @override_settings(
        WASTE_GUIDE_URL="https://waste.example/api",
        WASTE_GUIDE_API_KEY="test-key",
        ENVIRONMENT_SLUG="a",
    )
    def test_get_bag_nummeraanduiding_data_request_exception(self):
        """Return an empty list when waste-guide requests fail."""
        with patch.object(
            WasteDeviceService,
            "make_get_request",
            side_effect=requests.RequestException("network error"),
        ):
            result = self.service.get_bag_nummeraanduiding_data("bag_123")

        self.assertEqual(result, [])

    def test_make_get_request(self):
        """Perform a GET request and return parsed JSON content."""
        mocked_response = Mock()
        mocked_response.json.return_value = {"ok": True}

        with patch(
            "core.services.waste_device.requests.request", return_value=mocked_response
        ) as mocked_request:
            result = self.service.make_get_request(
                url="https://waste.example/api",
                headers={"X-Api-Key": "test"},
                params={"bagNummeraanduidingId": "bag_123"},
            )

        mocked_request.assert_called_once_with(
            method="GET",
            url="https://waste.example/api",
            headers={"X-Api-Key": "test"},
            params={"bagNummeraanduidingId": "bag_123"},
        )
        mocked_response.raise_for_status.assert_called_once()
        self.assertEqual(result, {"ok": True})
