from datetime import timedelta
from unittest.mock import patch

import freezegun
from django.contrib.auth.models import User
from django.utils import timezone
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models.notification_models import Device, ScheduledNotification
from notification.models.waste_guide_models import WasteDevice
from waste.models import ManualNotification
from waste.services.notification import ManualNotificationService, NotificationService
from waste.services.waste_collection import WasteCollectionService


@freezegun.freeze_time("2021-08-01")
class NotificationServiceTest(ResponsesActivatedAPITestCase):
    def test_call_notification_service(self):
        notification_service = NotificationService()
        notification_service.send(
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
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.notification_service = ManualNotificationService()

        postal_areas = {"1": "1011", "2": "1012", "3": "1012"}
        for suffix in ["1", "2", "3"]:
            Device.objects.create(
                external_id=f"device{suffix}", os="ios", firebase_token=None
            )
            WasteDevice.objects.create(
                device_id=f"device{suffix}",
                bag_nummeraanduiding_id=f"bag-{suffix}",
                postal_area=postal_areas[suffix],
            )

    def _create_device(self, external_id):
        return baker.make(
            Device, external_id=external_id, os="ios", firebase_token=None
        )

    def test_call_notification_service(self):
        scheduled_for = timezone.now() + timedelta(days=1)
        notification = ManualNotification.objects.create(
            title="Vanaf morgen kun je de kerstbook aan de straat zetten",
            message="Zorg dat je hem op de goede plek zet",
            created_by=self.user,
            send_at=scheduled_for,
        )

        self.notification_service.send(notification=notification)

        notification.refresh_from_db()
        scheduled_notification = ScheduledNotification.objects.get()
        self.assertEqual(
            scheduled_notification.title,
            "Vanaf morgen kun je de kerstbook aan de straat zetten",
        )
        self.assertEqual(
            scheduled_notification.body, "Zorg dat je hem op de goede plek zet"
        )
        self.assertEqual(scheduled_notification.module_slug, "waste-guide")
        self.assertEqual(
            scheduled_notification.notification_type, "waste-guide:manual-notification"
        )
        self.assertEqual(scheduled_notification.scheduled_for, scheduled_for)
        self.assertEqual(
            scheduled_notification.identifier,
            self.notification_service._create_identifier(notification.id),
        )
        self.assertEqual(notification.send_at, scheduled_for)
        self.assertEqual(notification.nr_sessions, 3)
        devices = set(
            scheduled_notification.devices.values_list("external_id", flat=True)
        )
        self.assertEqual(devices, {"device1", "device2", "device3"})

    def test_call_notification_service_updates_existing_schedule(self):
        initial_send_at = timezone.now() + timedelta(days=1)
        updated_send_at = initial_send_at + timedelta(hours=2)
        notification = ManualNotification.objects.create(
            title="Eerste titel",
            message="Eerste bericht",
            created_by=self.user,
            send_at=initial_send_at,
        )

        self.notification_service.send(notification=notification)

        notification.title = "Bijgewerkte titel"
        notification.message = "Bijgewerkt bericht"
        notification.send_at = updated_send_at
        notification.save(update_fields=["title", "message", "send_at"])

        self.notification_service.send(notification=notification)

        scheduled_notification = ScheduledNotification.objects.get()
        self.assertEqual(ScheduledNotification.objects.count(), 1)
        self.assertEqual(scheduled_notification.title, "Bijgewerkte titel")
        self.assertEqual(scheduled_notification.body, "Bijgewerkt bericht")
        self.assertEqual(scheduled_notification.scheduled_for, updated_send_at)
        self.assertEqual(
            scheduled_notification.identifier,
            self.notification_service._create_identifier(notification.id),
        )

    def test_delete_notification_removes_existing_schedule(self):
        notification = baker.make(
            ManualNotification,
            created_by=self.user,
            send_at=timezone.now() + timedelta(days=1),
        )

        self.notification_service.send(notification=notification)

        self.notification_service.delete_notification(notification)

        self.assertFalse(ScheduledNotification.objects.exists())

    def test_error_raised_if_notification_not_saved(self):
        notification = ManualNotification(
            title="Test",
            message="Test message",
            created_by=self.user,
            send_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(ValueError):
            self.notification_service._create_identifier(notification.id)

    def test_call_notification_service_filters_on_postal_area(self):
        scheduled_for = timezone.now() + timedelta(days=1)
        notification = ManualNotification.objects.create(
            title="Alleen gebied 1011",
            message="Bericht voor een postcodegebied",
            created_by=self.user,
            send_at=scheduled_for,
            affected_postal_area="1011",
        )

        self.notification_service.send(notification=notification)

        notification.refresh_from_db()
        self.assertEqual(notification.nr_sessions, 1)

        scheduled_notification = ScheduledNotification.objects.get()
        devices = set(
            scheduled_notification.devices.values_list("external_id", flat=True)
        )
        self.assertEqual(devices, {"device1"})

    def test_process_batch_counts_updated_skipped_and_has_more(self):
        """Track updated and skipped rows and return pagination metadata for a batch."""
        self._create_device("batch_a")
        self._create_device("batch_b")
        self._create_device("batch_c")
        baker.make(WasteDevice, device_id="batch_a")
        baker.make(WasteDevice, device_id="batch_b")
        baker.make(WasteDevice, device_id="batch_c")

        with patch.object(
            ManualNotificationService,
            "fill_empty_row",
            side_effect=[True, False],
        ):
            result = self.notification_service.process_batch(batch_size=2)

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
            ManualNotificationService,
            "fill_empty_row",
            side_effect=Exception("boom"),
        ):
            result = self.notification_service.process_batch(batch_size=1)

        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["last_pk"], "batch_failing")
        self.assertTrue(result["has_more"])

    def test_process_batch_returns_empty_result_when_no_rows(self):
        """Return an empty-batch response when there are no rows to process."""
        result = self.notification_service.process_batch(
            batch_size=5, last_pk="non_existing"
        )

        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["last_pk"], "non_existing")
        self.assertFalse(result["has_more"])

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
            WasteCollectionService,
            "get_validated_data_for_bag_id",
            return_value=[
                {
                    "code": "gft",
                    "route_name": "Route A",
                    "postal_code": "1091AB",
                }
            ],
        ):
            result = self.notification_service.fill_empty_row(waste_device)

        waste_device.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(waste_device.route_name_organic, "Route A")
        self.assertEqual(waste_device.postal_area, "1091")
        self.assertIsNotNone(waste_device.routes_updated_at)

    def test_fill_empty_row_without_bag_id(self):
        """Skip row update when bag_nummeraanduiding_id is missing."""
        self._create_device("missing_bag_device")
        waste_device = baker.make(
            WasteDevice,
            device_id="missing_bag_device",
            bag_nummeraanduiding_id=None,
            routes_updated_at=None,
        )

        result = self.notification_service.fill_empty_row(waste_device)

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
            WasteCollectionService,
            "get_validated_data_for_bag_id",
            return_value=[],
        ):
            result = self.notification_service.fill_empty_row(waste_device)

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
            WasteCollectionService,
            "get_validated_data_for_bag_id",
            return_value=[
                {
                    "code": "unknown",
                    "route_name": "Route X",
                    "postal_code": None,
                }
            ],
        ):
            result = self.notification_service.fill_empty_row(waste_device)

        waste_device.refresh_from_db()
        self.assertFalse(result)
        self.assertIsNone(waste_device.routes_updated_at)
