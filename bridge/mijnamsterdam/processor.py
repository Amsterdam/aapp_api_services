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
        self.notification_types = [n.value for n in NotificationType]

    def run(self):
        data = self.collect_notification_data()
        notification_type = f"{Module.MIJN_AMS.value}:mijn-ams-notification"
        self.notification_service.notification_type = notification_type
        for user_data in data:
            self.send_notification(user_data=user_data)

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

    def send_notification(self, *, user_data: dict):
        device_ids = user_data[
            "consumerIds"
        ]  # Multiple devices are possible per user (BSN)
        last_timestamp_per_device = self._get_last_timestamp_per_device(device_ids)
        make_push = self._get_push_enabled()

        for device in device_ids:
            last_timestamp = last_timestamp_per_device[device]
            nr_messages = self._get_nr_new_messages(last_timestamp, user_data)

            if nr_messages == 0:
                continue
            if nr_messages == 1:
                message = "U heeft een nieuw bericht op Mijn Amsterdam"
            else:
                message = f"U heeft {nr_messages} nieuwe berichten op Mijn Amsterdam"
            message += ". Ga naar Mijn Amsterdam."
            notification_data = NotificationData(
                link_source_id="mijn-amsterdam-id-placeholder",
                title="Mijn Amsterdam",
                message=message,
                device_ids=[device],
                make_push=make_push,
            )
            self.notification_service.send(notification_data=notification_data)

    def _get_push_enabled(self):
        """Placeholder for push notification logic"""
        return True

    def _get_last_timestamp_per_device(
        self, device_ids: list[str]
    ) -> dict[str, datetime]:
        last_timestamp_per_device = {}
        for id in device_ids:
            last_timestamp = self.notification_service.get_last_timestamp(device_id=id)
            last_timestamp_per_device[id] = last_timestamp or datetime(
                1900, 1, 1, tzinfo=timezone.utc
            )
        return last_timestamp_per_device

    def _get_nr_new_messages(self, last_timestamp, user_data):
        nr_messages = 0
        for service in user_data["services"]:
            nr_messages = len(
                [c for c in service["content"] if c["datePublished"] > last_timestamp]
            )
            nr_messages += nr_messages
        return nr_messages
