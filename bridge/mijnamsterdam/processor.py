import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from django.conf import settings

from bridge.mijnamsterdam.serializers.general_serializers import (
    MijnAmsNotificationResponseSerializer,
)
from bridge.mijnamsterdam.services.notifications import NotificationService
from core.enums import Module, NotificationType
from core.services.notification_service import NotificationData

logger = logging.getLogger(__name__)


class MijnAmsterdamNotificationProcessor:
    def __init__(self):
        self.notification_service = NotificationService()
        self.last_timestamp_per_device = {}
        self.notification_types = [n.value for n in NotificationType]

    def run(self):
        data = self.collect_notification_data()
        for user_data in data:
            device_ids = user_data[
                "consumerIds"
            ]  # Multiple devices are possible per user (BSN)
            self.get_last_timestamp_per_device(device_ids)
            self.send_notifications(user_data=user_data, device_ids=device_ids)

    def collect_notification_data(self) -> list[dict]:
        url = urljoin(
            settings.MIJN_AMS_API_DOMAIN, settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"]
        )
        response = requests.get(
            url,
            headers={
                settings.MIJN_AMS_API_KEY_HEADER: settings.MIJN_AMS_API_KEY_INBOUND
            },
        )
        response.raise_for_status()
        serializer = MijnAmsNotificationResponseSerializer(data=response.json())
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data["content"]

    def get_last_timestamp_per_device(self, device_ids: list[str]):
        for id in device_ids:
            if self.last_timestamp_per_device.get(id):
                logger.warning(
                    "Device id linked to multiple users", extra={"device_id": id}
                )
            last_timestamp = self.notification_service.get_last_timestamp(device_id=id)
            self.last_timestamp_per_device[id] = last_timestamp or datetime(
                1900, 1, 1, tzinfo=timezone.utc
            )

    def send_notifications(self, *, user_data: dict, device_ids: list[str]):
        make_push = self._get_push_enabled()
        for service in user_data["services"]:
            nr_messages = len(service["content"])
            if nr_messages == 0:
                continue

            service_id = service["serviceId"]
            notification_type = f"{Module.MIJN_AMS.value}:mijn-ams-notification"
            if notification_type not in self.notification_types:
                logger.warning(
                    "Received notification type not supported",
                    extra={"type": notification_type},
                )
                continue

            device_ids_to_send = self._get_device_ids_to_send(
                device_ids, date_published=service["dateUpdated"]
            )
            compounded_id = "-".join(
                [notification["id"] for notification in service["content"]]
            )[:150]
            if nr_messages == 1:
                message = f"U heeft een nieuw bericht over {service_id}"
            else:
                message = f"U heeft {nr_messages} nieuwe berichten over {service_id}"
            message += ". Ga naar Mijn Amsterdam."
            notification_data = NotificationData(
                link_source_id=compounded_id,
                title="Mijn Amsterdam",
                message=message,
                device_ids=device_ids_to_send,
                make_push=make_push,
            )
            self.notification_service.notification_type = notification_type
            self.notification_service.send(notification_data=notification_data)

    def _get_push_enabled(self):
        """Only send push if notification is newer than last active on MijnAmsterdam"""
        return True  # Placeholder for push notification logic

    def _get_device_ids_to_send(self, device_ids: list[str], date_published: datetime):
        """
        Get device ids where the last time a notification was sent
        is before the moment that the MijnAmsterdam notification was published.
        """
        devices_to_send = []
        for d in device_ids:
            last_timestamp = self.last_timestamp_per_device[d]
            is_new = last_timestamp < date_published
            if is_new:
                devices_to_send.append(d)
        return devices_to_send
