import datetime
import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from core.services.image_set import ImageSetService
from core.services.internal_http_client import InternalServiceSession
from core.services.notification_service import create_missing_device_ids
from notification.models import ScheduledNotification

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Exception raised for errors calling the Notification Service."""

    pass


class ScheduledNotificationService:
    def __init__(self):
        self.client = InternalServiceSession()
        self.image_service = ImageSetService()

    def upsert(
        self,
        title: str,
        body: str,
        scheduled_for: datetime,
        identifier: str,
        context: dict,
        device_ids: list[str],
        notification_type: str,
        module_slug: str = None,
        image: str = None,
        expires_at: datetime = None,
    ):
        devices = create_missing_device_ids(device_ids)
        if expires_at and expires_at <= scheduled_for:
            raise NotificationServiceError(
                "Expires_at must be later than scheduled_for"
            )
        if module_slug and not identifier.startswith(module_slug):
            raise NotificationServiceError("Identifier must start with module_slug")
        if image:
            if not self.image_service.exists(image):
                raise NotificationServiceError(f"Image with id {image} does not exist")

        instance = self._get_instance(identifier)
        # Perform CREATE if object does not exist
        if not instance:
            try:
                instance = ScheduledNotification(
                    title=title,
                    body=body,
                    scheduled_for=scheduled_for,
                    identifier=identifier,
                    context=context,
                    notification_type=notification_type,
                    module_slug=module_slug,
                    image=image,
                    created_at=timezone.now(),
                    expires_at=expires_at or "3000-01-01",
                )
                instance.save()
                instance.devices.set(devices)
                return instance
            except IntegrityError:
                # Handle race condition where another transaction created the same identifier
                instance = self._get_instance(identifier)

        # Perform UPDATE if object exists
        old_device_ids = list(instance.devices.all())
        devices = list(set(old_device_ids) | set(devices))  # Add new devices to old
        instance.title = title
        instance.body = body
        instance.scheduled_for = scheduled_for
        if image:
            instance.image = image
        if expires_at:
            instance.expires_at = expires_at
        with transaction.atomic():
            instance.save()
            instance.devices.set(devices)
        return instance

    def _get_instance(self, identifier):
        instance = ScheduledNotification.objects.filter(identifier=identifier).first()
        return instance

    def get_all(self) -> list[ScheduledNotification]:
        return list(ScheduledNotification.objects.all())

    def get(self, identifier: str) -> ScheduledNotification | None:
        try:
            instance = ScheduledNotification.objects.get(identifier=identifier)
            return instance
        except ScheduledNotification.DoesNotExist:
            return None

    def delete(self, identifier: str):
        try:
            ScheduledNotification.objects.get(identifier=identifier).delete()
        except ScheduledNotification.DoesNotExist:
            return None
