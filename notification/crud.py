import copy
import logging

from django.conf import settings
from django.db.models import Case, Exists, IntegerField, OuterRef, QuerySet, Value, When
from django.utils import timezone

from notification.models import (
    Device,
    Notification,
    NotificationLast,
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
)
from notification.services.push import PushService

logger = logging.getLogger(__name__)


class NotificationCRUD:
    def __init__(
        self,
        source_notification: Notification,
        push_enabled: bool = True,
    ):
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
        self.notifications_with_push, self.notifications_without_push = [], []
        self.devices_for_push = []
        self.push_service = PushService() if push_enabled else None

    def create(self, device_qs: QuerySet):
        """
        Create a new notification for each device in the supplied queryset.
        Push the notification to Firebase if applicable.

        device_ids (list[str]): All devices who want to receive a notification
        """
        device_list = self._collect_and_annotate_devices(device_qs)
        self.total_device_count = len(device_list)
        notifications_with_push = self._create_notifications(device_list)
        self._update_last_timestamps(device_list)

        if notifications_with_push and self.push_service:
            try:
                self.failed_token_count = self.push_service.push(
                    notifications=notifications_with_push
                )
            except Exception as e:
                logger.error("Failed to push notification", exc_info=True)
                raise e
        else:
            logger.info("Notification(s) created, but no devices to push to")

    def _collect_and_annotate_devices(self, device_qs: QuerySet) -> list[Device]:
        """
        This function should execute a single database query, to get all devices
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
        devices_for_push = []
        self.total_token_count = 0
        for device in device_list:
            if device.has_token:
                self.total_token_count += 1
            if (
                device.has_token
                and not device.module_disabled
                and not device.type_disabled
            ):
                devices_for_push.append(device)

        self.devices_for_push = devices_for_push
        self.total_enabled_count = len(devices_for_push)
        return device_list

    def _create_notifications(self, device_list: list[Device]) -> list[Notification]:
        """
        The supplied source_notification will be duplicated for every device.

        Returns:
            list[Notification]: newly created notification objects that should be pushed
        """
        self.source_notification.id = None
        with_push, without_push = [], []
        for c in device_list:
            new_notification: Notification = copy.copy(self.source_notification)
            new_notification.device = c
            if c in self.devices_for_push and self.push_service:
                new_notification.pushed_at = timezone.now()
                with_push.append(new_notification)
            else:
                without_push.append(new_notification)

        self.notifications_with_push = Notification.objects.bulk_create(with_push)
        self.notifications_without_push = Notification.objects.bulk_create(without_push)
        return self.notifications_with_push

    def _update_last_timestamps(self, device_list: list[Device]) -> None:
        """
        Update the last timestamps for all devices.
        This is used to determine when the last notification was created
        """
        if (
            self.source_notification.module_slug
            not in settings.NOTIFICATION_MODULE_SLUG_LAST_TIMESTAMP
        ):
            return

        notifications_last = [
            NotificationLast(
                device=device,
                module_slug=self.source_notification.module_slug,
                notification_scope=self.source_notification.notification_type,
            )
            for device in device_list
        ]
        NotificationLast.objects.bulk_create(
            notifications_last,
            update_fields=["last_create"],
            unique_fields=["device", "notification_scope"],
            update_conflicts=True,
        )

    @property
    def response_data(self):
        return dict(
            total_device_count=self.total_device_count,
            total_token_count=self.total_token_count,
            total_enabled_count=self.total_enabled_count,
            failed_token_count=self.failed_token_count,
        )
