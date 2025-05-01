import copy
import logging

from django.conf import settings
from django.db.models import Case, Exists, IntegerField, OuterRef, QuerySet, Value, When

from notification.models import (
    Device,
    Notification,
    NotificationLast,
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
)
from notification.services.push import PushService

logger = logging.getLogger(__name__)


class NotificationCRUDDeviceLimitError(Exception):
    """Raise when too many devices were passed"""

    pass


class NotificationCRUD:
    def __init__(self, source_notification: Notification) -> None:
        """
        The source notification is used to create a new notification for each device.

        The supplied source_notification comes with a UUID id,
        this is reset in order to use it for duplication.

        Args:
            source_notification (Notification): Source of new notifications

        Raises:
            PushServiceDeviceLimitError: Firebase cannot handle this many devices
        """
        self.source_notification = source_notification
        self.total_device_count = 0
        self.total_token_count = 0
        self.total_enabled_count = 0
        self.failed_token_count = 0

        self.push_service = PushService()

    def create(self, device_qs: QuerySet) -> dict:
        """
        Create a new notification for each device in the supplied queryset.
        Push the notification to Firebase if applicable.

        device_ids (list[str]): All devices who want to receive a notification
        """
        device_list, enabled_devices = self.get_enabled_devices_for_notification(
            device_qs
        )
        notifications_with_push, _ = self.create_notifications(
            device_list, enabled_devices
        )
        self.update_last_timestamps(device_list)

        if not notifications_with_push:
            logger.info("Notification(s) created, but no devices to push to")
            return self._response_data
        self.failed_token_count = self.push_service.push(notifications_with_push)
        return self._response_data

    def get_enabled_devices_for_notification(
        self, device_qs: QuerySet
    ) -> (list[Device], list[Device]):
        """
        This function should execute a single database query, to get all enabled devices
        """
        module_disabled_exists = NotificationPushModuleDisabled.objects.filter(
            device=OuterRef("pk"), module_slug=self.source_notification.module_slug
        )
        type_disabled_exists = NotificationPushTypeDisabled.objects.filter(
            device=OuterRef("pk"),
            notification_type=self.source_notification.notification_type,
        )
        annotated_devices = device_qs.annotate(
            has_token=Case(
                When(firebase_token__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            module_disabled=Exists(module_disabled_exists),
            type_disabled=Exists(type_disabled_exists),
        )

        device_list = list(annotated_devices)  # Database query is executed here
        max_devices = settings.FIREBASE_DEVICE_LIMIT
        if len(device_list) > max_devices:
            raise NotificationCRUDDeviceLimitError(
                f"Too many devices [{len(device_list)=}, {max_devices=}]"
            )
        self.total_device_count = len(device_list)

        enabled_devices = []
        self.total_token_count = 0
        for device in device_list:
            if device.has_token:
                self.total_token_count += 1
            if (
                device.has_token
                and not device.module_disabled
                and not device.type_disabled
            ):
                enabled_devices.append(device)

        self.total_enabled_count = len(enabled_devices)
        return device_list, enabled_devices

    def create_notifications(
        self, device_list: list[Device], enabled_device_list: list[Device]
    ) -> (list[Notification], list[Notification]):
        """
        The supplied source_notification will be duplicated for every device.

        Returns:
            list[Notification]: newly created notification objects
        """
        notifications_with_push, notifications_without_push = [], []
        self.source_notification.id = None
        for c in device_list:
            new_notification: Notification = copy.copy(self.source_notification)
            new_notification.device = c
            if c in enabled_device_list:
                notifications_with_push.append(new_notification)
            else:
                notifications_without_push.append(new_notification)

        notifications_with_push = Notification.objects.bulk_create(
            notifications_with_push
        )
        notifications_without_push = Notification.objects.bulk_create(
            notifications_without_push
        )
        return notifications_with_push, notifications_without_push

    def update_last_timestamps(self, device_list: list[Device]) -> None:
        """
        Update the last timestamps for all devices.
        This is used to determine when the last notification was created
        """
        notification_scope = self.source_notification.notification_type
        if notification_scope not in settings.NOTIFICATION_SCOPES:
            return

        notifications_last = [
            NotificationLast(
                device=device,
                module_slug=self.source_notification.module_slug,
                notification_scope=notification_scope,
            )
            for device in device_list
        ]
        NotificationLast.objects.bulk_create(
            notifications_last,
            update_fields=["last_create"],
            ignore_conflicts=True,
        )

    @property
    def _response_data(self):
        return dict(
            total_device_count=self.total_device_count,
            total_token_count=self.total_token_count,
            total_enabled_count=self.total_enabled_count,
            failed_token_count=self.failed_token_count,
        )
