import logging
import uuid
from datetime import datetime
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from core.services.image_set import ImageSetService
from core.services.notification_service import NotificationData, create_missing_device_ids
from notification.models import Device, Notification, NotificationLast, ScheduledNotification

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Exception raised for errors calling the Notification Service."""


class UnifiedNotificationService:
    """Unified service that supports both:

    - module-scoped notification creation via the `send()` + `process()` pattern
    - generic scheduled notification CRUD/upsert via `upsert()/get()/delete()`

    Existing services remain in place; this class is intended as a V2 replacement.
    """

    module_slug: str | None = None
    notification_type: str | None = None

    def __init__(self, use_image_service: bool = False, image_service: Any | None = None):
        self.link_source_id: str | None = None
        self.notification_url: str | None = None
        self.notification_deeplink: str | None = None

        if image_service is not None:
            self.image_service = image_service
        elif use_image_service:
            self.image_service = ImageSetService()
        else:
            self.image_service = None

    # --- read APIs (from AbstractNotificationService) ---

    def get_last_timestamp(self, device_id: str) -> datetime | None:
        timestamps = list(
            NotificationLast.objects.select_related("device").filter(
                device__external_id=device_id,
                module_slug=self._require_module_slug(),
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

    # --- module-scoped workflow (Abstract-like) ---

    def send(self, *args, **kwargs):
        raise NotImplementedError(
            "Subclasses must implement send() to create notifications."
        )

    def process(
        self,
        notification: NotificationData,
        expiry_minutes: int = 15,
        *,
        scheduled_for: datetime | str | None = None,
        expires_at: datetime | str | None = None,
        identifier: str | None = None,
        context: dict | None = None,
        module_slug: str | None = None,
        notification_type: str | None = None,
    ) -> ScheduledNotification:
        """Schedule a notification.

        Backwards compatible with existing `AbstractNotificationService.process()` by defaulting
        to `scheduled_for = now + 5s` and generating a random identifier.

        Also supports explicit scheduling parameters.
        """

        self.link_source_id = str(notification.link_source_id)
        self.notification_url = str(notification.url) if notification.url else None
        self.notification_deeplink = (
            str(notification.deeplink) if notification.deeplink else None
        )

        resolved_module_slug = module_slug or self.module_slug
        resolved_notification_type = notification_type or self.notification_type
        if not resolved_module_slug:
            raise NotificationServiceError("module_slug must be provided")
        if not resolved_notification_type:
            raise NotificationServiceError("notification_type must be provided")

        if identifier is None:
            identifier = f"{resolved_module_slug}_{uuid.uuid4()}"

        if scheduled_for is None:
            scheduled_for = timezone.now() + timezone.timedelta(seconds=5)

        if expires_at is None:
            expires_at = self._add_minutes(scheduled_for, expiry_minutes)

        if context is None:
            context = self.build_context(
                link_source_id=self.link_source_id,
                url=self.notification_url,
                deeplink=self.notification_deeplink,
                module_slug=resolved_module_slug,
                notification_type=resolved_notification_type,
            )

        return self.upsert(
            title=notification.title,
            body=notification.message,
            scheduled_for=scheduled_for,
            identifier=identifier,
            context=context,
            notification_type=resolved_notification_type,
            device_ids=notification.device_ids,
            module_slug=resolved_module_slug,
            image=notification.image_set_id,
            expires_at=expires_at,
            send_all_devices=False,
            make_push=notification.make_push,
        )

    def build_context(
        self,
        *,
        module_slug: str,
        notification_type: str,
        link_source_id: str | None = None,
        url: str | None = None,
        deeplink: str | None = None,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        context: dict[str, str] = {
            "type": str(notification_type),
            "module_slug": str(module_slug),
        }
        if link_source_id is not None:
            context["linkSourceid"] = str(link_source_id)
        if url is not None:
            context["url"] = str(url)
        if deeplink is not None:
            context["deeplink"] = str(deeplink)

        if extra:
            for key, value in extra.items():
                context[str(key)] = str(value)

        return context

    # --- scheduling CRUD + upsert (from ScheduledNotificationService) ---

    def upsert(
        self,
        *,
        title: str,
        body: str,
        scheduled_for: datetime | str,
        identifier: str,
        context: dict,
        notification_type: str,
        device_ids: list[str] | None = None,
        module_slug: str | None = None,
        image: str | int | None = None,
        expires_at: datetime | str | None = None,
        send_all_devices: bool = False,
        make_push: bool = True,
    ) -> ScheduledNotification:
        resolved_module_slug = module_slug or self.module_slug
        resolved_notification_type = notification_type or self.notification_type
        if not resolved_notification_type:
            raise NotificationServiceError("notification_type must be provided")

        if send_all_devices:
            devices = Device.objects.all()
        else:
            if device_ids is None:
                raise NotificationServiceError(
                    "Device ids must be defined if send_all_devices is False"
                )
            devices = create_missing_device_ids(device_ids)

        scheduled_for_dt = self._normalize_dt(scheduled_for)
        expires_at_dt = self._normalize_dt(expires_at) if expires_at is not None else None
        if expires_at_dt and scheduled_for_dt and expires_at_dt <= scheduled_for_dt:
            raise NotificationServiceError("Expires_at must be later than scheduled_for")

        if resolved_module_slug and not identifier.startswith(resolved_module_slug):
            raise NotificationServiceError("Identifier must start with module_slug")

        if image is not None:
            if self.image_service is None:
                raise NotificationServiceError(
                    "Image validation requires use_image_service=True"
                )
            if not self.image_service.exists(image):
                raise NotificationServiceError(f"Image with id {image} does not exist")

        instance = self._get_instance(identifier)
        if not instance:
            try:
                instance = ScheduledNotification(
                    title=title,
                    body=body,
                    scheduled_for=scheduled_for_dt or scheduled_for,
                    identifier=identifier,
                    context=context,
                    notification_type=str(resolved_notification_type),
                    module_slug=str(resolved_module_slug or ""),
                    image=image,
                    created_at=timezone.now(),
                    expires_at=expires_at_dt or expires_at or "3000-01-01",
                    make_push=make_push,
                )
                instance.save()
                instance.devices.set(devices)
                return instance
            except IntegrityError:
                instance = self._get_instance(identifier)

        old_devices = list(instance.devices.all())
        devices = list(set(old_devices) | set(devices))

        instance.title = title
        instance.body = body
        instance.scheduled_for = scheduled_for_dt or scheduled_for
        instance.context = context
        instance.notification_type = str(resolved_notification_type)
        if resolved_module_slug is not None:
            instance.module_slug = str(resolved_module_slug)
        if image is not None:
            instance.image = image
        if expires_at is not None:
            instance.expires_at = expires_at_dt or expires_at
        instance.make_push = make_push

        with transaction.atomic():
            instance.save()
            instance.devices.set(devices)

        return instance

    def _get_instance(self, identifier: str) -> ScheduledNotification | None:
        return ScheduledNotification.objects.filter(identifier=identifier).first()

    def get_all(self) -> list[ScheduledNotification]:
        return list(ScheduledNotification.objects.all())

    def get(self, identifier: str) -> ScheduledNotification | None:
        try:
            return ScheduledNotification.objects.get(identifier=identifier)
        except ScheduledNotification.DoesNotExist:
            return None

    def delete(self, identifier: str):
        try:
            ScheduledNotification.objects.get(identifier=identifier).delete()
        except ScheduledNotification.DoesNotExist:
            return None

    # --- helpers ---

    def _require_module_slug(self) -> str:
        if not self.module_slug:
            raise NotificationServiceError("module_slug must be set on the service")
        return str(self.module_slug)

    def _normalize_dt(self, value: datetime | str | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        # Let Django handle parsing via DateTimeField to_python by assigning to model,
        # but we need a datetime for comparisons.
        try:
            from django.utils.dateparse import parse_datetime

            parsed = parse_datetime(value)
            if parsed is None:
                return None
            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed
        except Exception:
            return None

    def _add_minutes(self, scheduled_for: datetime | str, minutes: int) -> datetime:
        scheduled_for_dt = self._normalize_dt(scheduled_for)
        if scheduled_for_dt is None:
            raise NotificationServiceError("scheduled_for must be a datetime")
        return scheduled_for_dt + timezone.timedelta(minutes=minutes)
