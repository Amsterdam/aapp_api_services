import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from django.conf import settings

from bridge.mijnamsterdam.serializers.general_serializers import (
    MijnAmsNotificationResponseSerializer,
    UserSerializer,
)
from bridge.mijnamsterdam.services.notifications import NotificationService
from core.enums import NotificationType
from core.services.notification import NotificationData

logger = logging.getLogger(__name__)


class MijnAmsterdamNotificationProcessor:
    def __init__(self):
        self.notification_service = NotificationService()
        self.last_timestamp_per_device = {}

    def run(self):
        data = self.collect_notification_data()
        for user_data in data:
            device_ids = user_data[
                "consumer_ids"
            ]  # Multiple devices are possible per user (BSN)
            self.get_last_timestamp_per_device(device_ids)
            self.send_notifications(user_data=user_data, device_ids=device_ids)

    def collect_notification_data(self) -> MijnAmsNotificationResponseSerializer:
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
            last_timestamp = self.notification_service.get_last_timestamp(id)
            self.last_timestamp_per_device[id] = last_timestamp or datetime(
                1900, 1, 1, tzinfo=timezone.utc
            )

    def send_notifications(self, *, user_data: UserSerializer, device_ids: list[str]):
        make_push = self._make_push()
        for notification in user_data["notifications"]:
            device_ids_to_send = self._get_device_ids_to_send(
                device_ids, date_published=notification["datePublished"]
            )
            notification_data = NotificationData(
                link_source_id=notification["id"],
                title="Mijn Amsterdam melding",
                message=notification["title"],
                device_ids=device_ids_to_send,
                make_push=make_push,
                # TODO: using a custom scope does not work with the notification service!
                # Since NotificationCRUD._update_last_timestamps checks is the notifiction scope is known in "settings.NOTIFICATION_SCOPES",
                # so creating a scope in runtime does not match with that logic.
                # Either have a static scope, which will disabled the option to check if notification for a specific type (e.g. belasying) has already been sent
                # Or dynamically add scope to the settings.NOTIFICATION_SCOPES, which would go against it being a Enum
                # Or something else...
                # notification_scope=f"{Module.MIJN_AMS.value}:{user_data['service_ids'][0]}",
                # This is TMP fix to make the integation test work so I can continue merging PRs for other services
                notification_scope=NotificationType.MIJN_AMS_NOTIFICATION.value,
            )
            self.notification_service.send(notification_data=notification_data)

    def _make_push(self):
        """Only send push if notification is newer than last active on MijnAmsterdam"""
        return True  # Placeholder for push notification logic

    def _get_device_ids_to_send(self, device_ids: list[str], date_published: datetime):
        """
        Get device ids where the last time a notification was sent
        is before the moment that the MijnAmsterdam notification was published.
        """
        return [
            d for d in device_ids if self.last_timestamp_per_device[d] < date_published
        ]
