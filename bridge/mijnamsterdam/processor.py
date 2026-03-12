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
from core.services.notification_service import (
    NotificationData,
    create_missing_device_ids,
)

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
            try:
                logger.info(f"Processing user device_ids {user_data['consumerIds']}")
                create_missing_device_ids(device_ids=user_data["consumerIds"])
                self.send_notifications(user_data=user_data)
            except Exception as e:
                logger.error(
                    f"Error processing notifications for user {user_data['consumerIds']}",
                    exc_info=e,
                )

    def collect_notification_data(self) -> list[dict]:
        batch_size = 100  # users per batch, adjust as needed
        notification_data = []
        offset = 0
        while True:
            new_data = self.collect_notification_batch(offset=offset, limit=batch_size)
            if not new_data:
                return notification_data
            notification_data.extend(new_data)
            offset += batch_size

    def collect_notification_batch(self, offset: int, limit: int) -> list[dict]:
        url = urljoin(
            settings.MIJN_AMS_API_DOMAIN, settings.MIJN_AMS_API_PATHS["NOTIFICATIONS"]
        )
        response = requests.get(
            url,
            params={"offset": offset, "limit": limit},
            headers={
                settings.MIJN_AMS_API_KEY_HEADER: settings.MIJN_AMS_API_KEY_INBOUND
            },
        )
        response.raise_for_status()
        serializer = MijnAmsNotificationResponseSerializer(data=response.json())
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data["content"]

    def send_notifications(self, *, user_data: dict):
        device_ids = user_data[
            "consumerIds"
        ]  # Multiple devices are possible per user (BSN)
        make_push = self._get_push_enabled()

        for device in device_ids:
            logger.info("Processing device", extra={"device_id": device})
            last_timestamps = self.notification_service.get_last_timestamps(
                device_id=device
            )
            nr_messages_total, ts_updates = self.get_nr_messages(
                last_timestamps, user_data
            )

            self._send_notification(device, make_push, nr_messages_total)
            if ts_updates:
                self.notification_service.update_last_timestamps(
                    device_id=device, updates=ts_updates
                )

    def _send_notification(self, device, make_push, nr_messages_total):
        if nr_messages_total == 0:
            return
        if nr_messages_total == 1:
            message = "U heeft een nieuw bericht op Mijn Amsterdam"
        else:
            message = f"U heeft {nr_messages_total} nieuwe berichten op Mijn Amsterdam"
        message += ". Ga naar Mijn Amsterdam."
        notification_data = NotificationData(
            link_source_id="mijn-amsterdam-id-placeholder",
            title="Mijn Amsterdam",
            message=message,
            device_ids=[device],
            make_push=make_push,
        )
        logger.info(f"Sending notification for {nr_messages_total} new messages")
        self.notification_service.send(notification_data=notification_data)

    def _get_push_enabled(self):
        """Placeholder for push notification logic"""
        return True

    def get_nr_messages(self, last_timestamps, user_data):
        nr_messages_total = 0
        ts_updates = {}
        for service in user_data["services"]:
            service_id = service["serviceId"]
            last_ts = last_timestamps.get(service_id)
            logger.info(
                "Comparing data with last timestamp",
                extra={"service_id": service_id, "last_timestamp": last_ts},
            )
            nr_svc_messages, new_last_ts = self.get_nr_service_messages(
                last_ts, service
            )
            ts_updates[service_id] = new_last_ts
            if last_ts:
                # Only register new messages if we have a last timestamp, otherwise we are processing the user for
                # the first time and should not send notifications for all existing messages
                nr_messages_total += nr_svc_messages
        return nr_messages_total, ts_updates

    def get_nr_service_messages(self, last_timestamp, service) -> (int, datetime):
        nr_svc_messages = 0
        new_last_timestamp = datetime(1970, 1, 1, tzinfo=timezone.utc)
        for c in service["content"]:
            date_published = c["datePublished"]
            if not last_timestamp or date_published > last_timestamp:
                nr_svc_messages += 1
                new_last_timestamp = max(new_last_timestamp, date_published)
                logger.debug(
                    "New message found",
                    extra={
                        "service": service["serviceId"],
                        "published_at": date_published,
                    },
                )
        return nr_svc_messages, new_last_timestamp
