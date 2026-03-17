import logging
import uuid
from datetime import datetime
from typing import NamedTuple

from django.db import transaction
from django.utils import timezone
from more_itertools import chunked

from core.services.image_set import ImageSetService
from notification.models import (
    Device,
    Notification,
    ScheduledNotification,
)

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Exception raised for errors calling the Notification Service."""


class NotificationData(NamedTuple):
    title: str
    message: str
    link_source_id: str | None = None
    device_ids: list[str] | None = None
    image_set_id: int | None = None
    make_push: bool = True
    url: str | None = None
    deeplink: str | None = None


class AbstractNotificationService:
    """Unified service that supports both:

    - module-scoped notification creation via the `send()` + `upsert()` pattern
    - generic scheduled notification CRUD/upsert via `upsert()/get()/delete()`
    """

    module_slug: str | None = None
    notification_type: str | None = None

    def __init__(self, use_image_service: bool = False):
        if use_image_service:
            self.image_service = ImageSetService()
        else:
            self.image_service = None

        # check that both module slug and notification type are set
        if self.module_slug is None:
            raise NotificationServiceError("module_slug must be set on the service")
        if self.notification_type is None:
            raise NotificationServiceError(
                "notification_type must be set on the service"
            )

    def send(self, *args, **kwargs):
        """
        Send a notification to users based on the provided notification data.
        This method should be overridden by subclasses to implement specific notification logic.
        The 'upsert' method should be called with the notification data.
        """
        raise NotImplementedError(
            "Subclasses must implement the send method to upsert notifications."
        )

    def upsert(
        self,
        notification: NotificationData,
        identifier: str | None = None,
        context: dict | None = None,
        scheduled_for: datetime | None = None,
        expires_at: datetime | None = None,
        expiry_minutes: int = 15,
        send_all_devices: bool = False,
    ) -> ScheduledNotification:
        if identifier is None:
            identifier = f"{self.module_slug}_{uuid.uuid4()}"

        if context is None:
            context = self.build_context(
                module_slug=self.module_slug,
                notification_type=self.notification_type,
                link_source_id=notification.link_source_id,
                url=notification.url,
                deeplink=notification.deeplink,
            )

        if scheduled_for is None:
            scheduled_for = timezone.now() + timezone.timedelta(seconds=5)

        if expires_at is None:
            expires_at = scheduled_for + timezone.timedelta(minutes=expiry_minutes)

        if send_all_devices:
            device_ids = list(Device.objects.values_list("id", flat=True))
        else:
            if notification.device_ids is None:
                raise NotificationServiceError(
                    "Device ids must be defined if send_all_devices is False"
                )
            device_ids = self.create_missing_device_ids(notification.device_ids)

        if expires_at and expires_at <= scheduled_for:
            raise NotificationServiceError(
                "Expires_at must be later than scheduled_for"
            )

        if not identifier.startswith(self.module_slug):
            raise NotificationServiceError("Identifier must start with module_slug")

        if notification.image_set_id is not None:
            if self.image_service is None:
                raise NotificationServiceError(
                    "Image validation requires use_image_service=True"
                )
            if not self.image_service.exists(notification.image_set_id):
                raise NotificationServiceError(
                    f"Image with id {notification.image_set_id} does not exist"
                )

        instance = self._get_scheduled_notification_instance(identifier)
        if not instance:
            instance = ScheduledNotification(
                title=notification.title,
                body=notification.message,
                scheduled_for=scheduled_for,
                identifier=identifier,
                context=context,
                notification_type=self.notification_type,
                module_slug=self.module_slug,
                image=notification.image_set_id,
                created_at=timezone.now(),
                expires_at=expires_at or "3000-01-01",
                make_push=notification.make_push,
            )
            instance.save()
            self._set_devices(device_ids, instance_id=instance.id)
            return instance

        # Perform UPDATE if object exists
        # Note: notification type, module slug, context and make_push are not updatable
        instance.title = notification.title
        instance.body = notification.message
        instance.scheduled_for = scheduled_for

        if notification.image_set_id is not None:
            instance.image = notification.image_set_id
        if expires_at is not None:
            instance.expires_at = expires_at

        with transaction.atomic():
            instance.save()
            self._set_devices(device_ids, instance_id=instance.id)

        return instance

    def _set_devices(self, devices: list[int], instance_id: int):
        # Inserting into the Through table is much less memory-intensive than instance.devices.set(devices)
        # Note: previously added devices will not be removed!
        Through = ScheduledNotification.devices.through
        for batch in chunked(devices, 5000):
            rows = (
                Through(
                    schedulednotification_id=instance_id,
                    device_id=device_id,
                )
                for device_id in batch
            )
            Through.objects.bulk_create(rows, batch_size=5000, ignore_conflicts=True)

    def build_context(
        self,
        module_slug: str,
        notification_type: str,
        link_source_id: str | None = None,
        url: str | None = None,
        deeplink: str | None = None,
    ) -> dict[str, str]:
        """Context can only contain string values!"""
        context = {
            "type": notification_type,
            "module_slug": module_slug,
        }
        if link_source_id is not None:
            context["linkSourceid"] = str(link_source_id)
        if url is not None:
            context["url"] = str(url)
        if deeplink is not None:
            context["deeplink"] = str(deeplink)

        return context

    def _get_scheduled_notification_instance(
        self, identifier: str
    ) -> ScheduledNotification | None:
        return ScheduledNotification.objects.filter(identifier=identifier).first()

    def get_notifications(self, device_id: str) -> list[Notification]:
        return (
            Notification.objects.select_related("device")
            .filter(device__external_id=device_id)
            .order_by("-created_at")
        )

    def get_all_scheduled_notifications(self) -> list[ScheduledNotification]:
        return list(ScheduledNotification.objects.all())

    def get_scheduled_notification(
        self, identifier: str
    ) -> ScheduledNotification | None:
        try:
            return ScheduledNotification.objects.get(identifier=identifier)
        except ScheduledNotification.DoesNotExist:
            return None

    def delete_scheduled_notification(self, identifier: str):
        try:
            ScheduledNotification.objects.get(identifier=identifier).delete()
        except ScheduledNotification.DoesNotExist:
            return None

    @staticmethod
    def create_missing_device_ids(device_ids: list[str]) -> list[int]:
        existing_devices = Device.objects.filter(
            external_id__in=device_ids
        ).values_list("external_id", flat=True)
        missing_device_ids = set(device_ids) - set(existing_devices)
        if missing_device_ids:
            Device.objects.bulk_create(
                Device(external_id=device_id) for device_id in missing_device_ids
            )
            logger.info(f"Created {len(missing_device_ids)} missing devices.")
        return list(
            Device.objects.filter(external_id__in=device_ids).values_list(
                "id", flat=True
            )
        )
