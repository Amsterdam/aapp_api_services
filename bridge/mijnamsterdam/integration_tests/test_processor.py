# import re
# from datetime import datetime, timedelta
# from typing import NamedTuple
# from urllib.parse import urljoin
#
# import pytest
# import responses
# from django.conf import settings
# from django.utils import timezone
#
# from bridge.mijnamsterdam.processor import MijnAmsterdamNotificationProcessor
# from core.tests.test_authentication import ResponsesActivatedAPITestCase
#
#
# class NotificationData(NamedTuple):
#     device_ids: list[str]
#     nr_of_notifications: int
#
#
# class TestMijnAmsterdamNotificationProcessor(ResponsesActivatedAPITestCase):
#     def setUp(self):
#         self.processor = MijnAmsterdamNotificationProcessor()
#         self.notification_service = self.processor.notification_service
#         responses.add_passthru(
#             re.compile(settings.NOTIFICATION_ENDPOINTS["NOTIFICATIONS"] + ".*")
#         )
#         responses.add_passthru(
#             re.compile(settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"] + ".*")
#         )
#         responses.add_passthru(
#             re.compile(settings.NOTIFICATION_ENDPOINTS["LAST_TIMESTAMP"] + ".*")
#         )
#
#     def test_run_processor_single(self):
#         device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         self._set_mock_data(
#             [NotificationData(device_ids=[device_id], nr_of_notifications=1)]
#         )
#         notifications = self.notification_service.get_notifications(device_id)
#         self.assertEqual(len(notifications), 0)
#
#         self.processor.run()
#
#         notifications = self.notification_service.get_notifications(device_id)
#         self.assertEqual(len(notifications), 1)
#
#     def test_run_processor_multiple(self):
#         device_id = (
#             f"integration_test_1_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         )
#         device_id_2 = (
#             f"integration_test_2_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         )
#         device_id_3 = (
#             f"integration_test_3_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         )
#         self._set_mock_data(
#             [
#                 NotificationData(
#                     device_ids=[device_id, device_id_2], nr_of_notifications=2
#                 ),
#                 NotificationData(device_ids=[device_id_3], nr_of_notifications=1),
#             ]
#         )
#
#         self.processor.run()
#
#         notifications = self.notification_service.get_notifications(device_id)
#         self.assertEqual(len(notifications), 2)
#         notifications = self.notification_service.get_notifications(device_id_2)
#         self.assertEqual(len(notifications), 2)
#         notifications = self.notification_service.get_notifications(device_id_3)
#         self.assertEqual(len(notifications), 1)
#
#     def test_run_processor_deduplicate(self):
#         device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         device_id_2 = (
#             f"integration_test_2_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         )
#         self._set_mock_data(
#             [
#                 NotificationData(
#                     device_ids=[device_id, device_id_2], nr_of_notifications=1
#                 )
#             ]
#         )
#         for _i in range(3):
#             self.processor.run()
#
#             notifications = self.notification_service.get_notifications(device_id)
#             self.assertEqual(len(notifications), 1)
#             notifications = self.notification_service.get_notifications(device_id_2)
#             self.assertEqual(len(notifications), 1)
#
#     def test_run_processor_consecutive(self):
#         device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         mock_data = self._set_mock_data(
#             [NotificationData(device_ids=[device_id], nr_of_notifications=1)]
#         )
#         for i in range(3):
#             self.processor.run()
#
#             notifications = self.notification_service.get_notifications(device_id)
#             self.assertEqual(len(notifications), i + 1)
#
#             # Set a new datePublished for each iteration, so every run has a new notification
#             mock_data["content"][0]["notifications"][0]["datePublished"] = (
#                 timezone.now().isoformat()
#             )
#             responses.get(
#                 urljoin(
#                     settings.MIJN_AMS_API_DOMAIN,
#                     settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
#                 ),
#                 json=mock_data,
#             )
#
#     def test_run_processor_developing_payload(self):
#         device_id = f"integration_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
#         mock_data = self._set_mock_data(
#             [NotificationData(device_ids=[device_id], nr_of_notifications=2)]
#         )
#
#         self.processor.run()
#
#         notifications = self.notification_service.get_notifications(device_id)
#         self.assertEqual(len(notifications), 2)
#
#         # Add another notification to the mock data, and make sure only the new one is processed
#         mock_data["content"][0]["notifications"].append(
#             {
#                 "id": "belasting-3",
#                 "title": "Betaal uw aanslag",
#                 "datePublished": timezone.now().isoformat(),
#             }
#         )
#         responses.get(
#             urljoin(
#                 settings.MIJN_AMS_API_DOMAIN,
#                 settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
#             ),
#             json=mock_data,
#         )
#
#         self.processor.run()
#
#         notifications = self.notification_service.get_notifications(device_id)
#         self.assertEqual(len(notifications), 3)
#
#     def _set_mock_data(self, data: list[NotificationData]):
#         mock_data = {
#             "content": [
#                 {
#                     "service_ids": ["belasting"],
#                     "consumer_ids": notification.device_ids,
#                     "date_updated": timezone.now().isoformat(),
#                     "notifications": [
#                         {
#                             "id": f"belasting-{i + 1}",
#                             "title": "Betaal uw aanslag",
#                             "datePublished": (
#                                 timezone.now() - timedelta(minutes=2)
#                             ).isoformat(),
#                         }
#                         for i in range(notification.nr_of_notifications)
#                     ],
#                 }
#                 for notification in data
#             ],
#             "status": "OK",
#         }
#         responses.get(
#             urljoin(
#                 settings.MIJN_AMS_API_DOMAIN,
#                 settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"],
#             ),
#             json=mock_data,
#         )
#         return mock_data
