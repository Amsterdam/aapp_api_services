from unittest.mock import patch

import freezegun
from django.contrib.auth.models import User
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models.notification_models import Device, ScheduledNotification
from notification.models.waste_guide_models import WasteDevice
from waste.models import ManualNotification, WasteCollectionRouteName
from waste.services.notification import ManualNotificationService, NotificationService


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

        for suffix in ["1", "2", "3"]:
            Device.objects.create(
                external_id=f"device{suffix}", os="ios", firebase_token=None
            )
            WasteDevice.objects.create(
                device_id=f"device{suffix}", bag_nummeraanduiding_id=f"bag-{suffix}"
            )

    def test_call_notification_service(self):

        notification = ManualNotification.objects.create(
            title="Vanaf morgen kun je de kerstbook aan de straat zetten",
            message="Zorg dat je hem op de goede plek zet",
            created_by=self.user,
        )
        self.notification_service.send(notification=notification)

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

    @patch.object(ManualNotificationService, "get_bag_ids_for_route_name")
    def test_call_notification_service_for_selected_routes(self, mock_get_bag_ids):

        route_a = baker.make(WasteCollectionRouteName, name="Route-A")

        mock_get_bag_ids.side_effect = lambda route_name: (
            ["bag-1", "bag-2"] if route_name == "Route-A" else ["bag-3"]
        )

        notification = ManualNotification.objects.create(
            title="Routebericht",
            message="Alleen geselecteerde route",
            created_by=self.user,
        )
        notification.affected_routes.set([route_a])

        self.notification_service.send(notification=notification)

        scheduled = ScheduledNotification.objects.first()
        devices = set(scheduled.devices.values_list("external_id", flat=True))
        self.assertEqual(devices, {"device1", "device2"})
        self.assertNotIn("device3", devices)
        self.assertEqual(notification.nr_sessions, 2)
        mock_get_bag_ids.assert_called_once_with("Route-A")

    @patch.object(ManualNotificationService, "get_bag_ids_for_route_name")
    def test_call_notification_service_for_multiple_routes(self, mock_get_bag_ids):

        route_a = baker.make(WasteCollectionRouteName, name="Route-A")
        route_b = baker.make(WasteCollectionRouteName, name="Route-B")

        mock_get_bag_ids.side_effect = lambda route_name: (
            ["bag-1", "bag-2"] if route_name == "Route-A" else ["bag-2", "bag-3"]
        )

        notification = ManualNotification.objects.create(
            title="Multi-route bericht",
            message="Meerdere routes",
            created_by=self.user,
        )
        notification.affected_routes.set([route_a, route_b])

        self.notification_service.send(notification=notification)

        scheduled = ScheduledNotification.objects.first()
        devices = set(scheduled.devices.values_list("external_id", flat=True))
        self.assertEqual(devices, {"device1", "device2", "device3"})
        self.assertEqual(notification.nr_sessions, 3)
        self.assertEqual(mock_get_bag_ids.call_count, 2)

    def test_get_bag_ids_for_route_name(self):
        """Test that the get_bag_ids_for_route_name method returns the expected bag IDs for a given route name."""
        first_page_url = "https://api.example.com/waste?page=1"
        second_page_url = "https://api.example.com/waste?page=2"

        with patch(
            "waste.services.notification.settings.WASTE_GUIDE_URL", first_page_url
        ):
            with patch.object(
                ManualNotificationService,
                "get_validated_data",
                side_effect=[
                    (
                        [
                            {"bag_nummeraanduiding_id": "bag-1"},
                            {"bag_nummeraanduiding_id": "bag-2"},
                            {"bag_nummeraanduiding_id": None},
                        ],
                        second_page_url,
                    ),
                    (
                        [
                            {"bag_nummeraanduiding_id": "bag-2"},
                            {"bag_nummeraanduiding_id": "bag-3"},
                            {"bag_nummeraanduiding_id": ""},
                        ],
                        None,
                    ),
                ],
            ) as mock_get_validated_data:
                bag_ids = self.notification_service.get_bag_ids_for_route_name(
                    "Route-A"
                )

        self.assertEqual(set(bag_ids), {"bag-1", "bag-2", "bag-3"})
        self.assertEqual(mock_get_validated_data.call_count, 2)
        self.assertEqual(
            mock_get_validated_data.call_args_list[0].kwargs,
            {
                "url": first_page_url,
                "params": {
                    "afvalwijzerRoutenaam": "Route-A",
                    "_pageSize": 20000,
                },
            },
        )
        self.assertEqual(
            mock_get_validated_data.call_args_list[1].kwargs,
            {
                "url": second_page_url,
                "params": None,
            },
        )
