import logging
import uuid
from datetime import datetime
from typing import NamedTuple

from django.utils import timezone

from core.enums import Module, NotificationType
from core.services.internal_http_client import InternalServiceSession
from notification.models import (
    Device,
    Notification,
    NotificationLast,
    ScheduledNotification,
)

logger = logging.getLogger(__name__)


class InternalServiceError(Exception):
    """Something went wrong calling the notification service"""


class NotificationData(NamedTuple):
    link_source_id: str
    title: str
    message: str
    device_ids: list[str]
    image_set_id: int = None
    make_push: bool = True
    url: str = None
    deeplink: str = None


class AbstractNotificationService:
    module_slug: Module = None
    notification_type: NotificationType = None

    def __init__(self):
        self.client = InternalServiceSession()
        self.link_source_id = None

    def get_last_timestamp(self, device_id: str) -> datetime | None:
        timestamps = list(
            NotificationLast.objects.select_related("device").filter(
                device__external_id=device_id,
                module_slug=self.module_slug,
            )
        )
        timestamps = [nt.last_create for nt in timestamps]
        return max(timestamps) if timestamps else None

    def get_notifications(self, device_id: str) -> list[Notification]:
        return (
            Notification.objects.select_related("device")
            .filter(device__external_id=device_id)
            .order_by("-created_at")
        )

    def send(self, *args, **kwargs):
        """
        Send a notification to users based on the provided notification data.
        This method should be overridden by subclasses to implement specific notification logic.
        The 'process' method should be called with the notification data.
        """
        raise NotImplementedError(
            "Subclasses must implement the send method to process notifications."
        )

    def process(
        self,
        notification: NotificationData,
        expiry_minutes: int = 15,
    ):
        """
        Send notifications to users.
        """
        self.link_source_id = notification.link_source_id
        self.notification_url = notification.url
        self.notification_deeplink = notification.deeplink
        devices = create_missing_device_ids(notification.device_ids)
        now = timezone.now() + timezone.timedelta(seconds=5)
        instance = ScheduledNotification(
            title=notification.title,
            body=notification.message,
            module_slug=self.module_slug,
            notification_type=self.notification_type,
            created_at=timezone.now(),
            context=self.get_context(),
            make_push=notification.make_push,
            scheduled_for=now,
            expires_at=now + timezone.timedelta(minutes=expiry_minutes),
            identifier=f"{self.module_slug}_{uuid.uuid4()}",
            image=notification.image_set_id,
        )
        instance.save()
        instance.devices.set(devices)

    def get_context(self) -> dict:
        """Context can only contain string values!"""
        context = {
            "linkSourceid": str(self.link_source_id),
            "type": self.notification_type,
            "module_slug": self.module_slug,
        }
        if self.notification_url:
            context["url"] = str(self.notification_url)
        if self.notification_deeplink:
            context["deeplink"] = str(self.notification_deeplink)
        return context


def create_missing_device_ids(device_ids: list[str]) -> list[Device]:
    existing_devices = Device.objects.filter(external_id__in=device_ids).values_list(
        "external_id", flat=True
    )
    missing_device_ids = set(device_ids) - set(existing_devices)
    if missing_device_ids:
        Device.objects.bulk_create(
            Device(external_id=device_id) for device_id in missing_device_ids
        )
        logger.info(f"Created {len(missing_device_ids)} missing devices.")
    return Device.objects.filter(external_id__in=device_ids)
