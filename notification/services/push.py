import copy
import json
import logging

import firebase_admin
from django.conf import settings
from django.db.models import Case, Exists, IntegerField, OuterRef, QuerySet, Value, When
from firebase_admin import credentials, messaging

from core.services.image_set import ImageSetService
from notification.models import (
    Device,
    Notification,
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
)

logger = logging.getLogger(__name__)


class PushServiceDeviceLimitError(Exception):
    """Raise when too many devices were passed"""

    pass


class PushService:
    def __init__(
        self, source_notification: Notification, devices_qs: QuerySet[Device]
    ) -> None:
        """
        First the Firebase admin will be initialized.
        Firebase manages its own connections, so when multiple services are initialized,
        Firebase will check if there is already an active connection setup.

        Next it will check for the limit of devices.

        Finally the supplied source_notification comes with a UUID id,
        this is reset in order to use it for duplication.

        Args:
            source_notification (Notification): Source of new notifications
            device_ids (list[str]): All devices who want to receive a notification

        Raises:
            PushServiceDeviceLimitError: Firebase cannot handle this many devices
        """
        if not firebase_admin._apps:
            creds = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
            firebase_admin.initialize_app(creds)
        else:
            firebase_admin.get_app()

        self.devices_qs = devices_qs
        self.source_notification = source_notification
        self.total_device_count = 0
        self.total_token_count = 0
        self.total_enabled_count = 0
        self.failed_token_count = 0

    def push(self) -> dict:
        device_list, enabled_devices = self.get_enabled_devices_for_notification()
        notifications_with_push, _ = self.create_notifications(
            device_list, enabled_devices
        )
        if not notifications_with_push:
            logger.info("Notification(s) created, but no devices to push to")
            return self._response_data

        self.push_messages(notifications_with_push)
        return self._response_data

    def get_enabled_devices_for_notification(self) -> (list[Device], list[Device]):
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
        annotated_devices = self.devices_qs.annotate(
            has_token=Case(
                When(firebase_token__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            module_disabled=Exists(module_disabled_exists),
            type_disabled=Exists(type_disabled_exists),
        )

        self.device_list = list(annotated_devices)  # Database query is executed here
        max_devices = settings.FIREBASE_DEVICE_LIMIT
        if len(self.device_list) > max_devices:
            raise PushServiceDeviceLimitError(
                f"Too many devices [{len(self.device_list)=}, {max_devices=}]"
            )
        self.total_device_count = len(self.device_list)

        enabled_devices = []
        self.total_token_count = 0
        for device in self.device_list:
            if device.has_token:
                self.total_token_count += 1
            if (
                device.has_token
                and not device.module_disabled
                and not device.type_disabled
            ):
                enabled_devices.append(device)

        self.total_enabled_count = len(enabled_devices)
        return self.device_list, enabled_devices

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

    def push_messages(self, notifications: list[Notification]):
        """
        Forwards notification to Firebase, to be pushed to devices.

        If device has a firebase token, a Firebase message will be crafted
        and finally send as a batch to Firebase.

        Args:
            notifications (list[Notification]): notifications used for Firebase message data
        """

        firebase_messages = [self._define_firebase_message(n) for n in notifications]
        batch_response = messaging.send_each(firebase_messages)
        if batch_response.failure_count > 0:
            self._log_failures(batch_response, firebase_messages)
        return

    def _define_firebase_message(
        self, notification_obj: Notification
    ) -> messaging.Message:
        complete_context = notification_obj.context
        complete_context["notificationId"] = str(notification_obj.pk)

        ios_image_config, android_image_config = None, None
        if notification_obj.image:
            image_set = ImageSetService()
            image_set.get(notification_obj.image)
            android_image_config, ios_image_config = self._get_image_config(image_set)

        firebase_message = messaging.Message(
            data=complete_context,
            notification=messaging.Notification(
                title=notification_obj.title, body=notification_obj.body
            ),
            token=notification_obj.device.firebase_token,
            android=android_image_config,
            apns=ios_image_config,
        )
        return firebase_message

    def _get_image_config(self, image_set: ImageSetService):
        """
        Image requirements:
        - Max size: 1 MB
        - Formats: JPEG, PNG, BMP
        - Width: 300px to 2000px
        - Height: at least 200px
        - Dimensions: landscape with 2:1 aspect ratio (e.g., 1000x500)
        """
        image_url = image_set.url_medium
        android_image_config = messaging.AndroidConfig(
            notification=messaging.AndroidNotification(image=image_url)
        )
        ios_image_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(aps=messaging.Aps(mutable_content=True)),
            fcm_options=messaging.APNSFCMOptions(image=image_url),
        )
        return android_image_config, ios_image_config

    def _log_failures(self, batch_response, firebase_messages: list[messaging.Message]):
        failed_tokens = []
        responses = batch_response.responses
        for idx, resp in enumerate(responses):
            if not resp.success:
                failed_token = firebase_messages[idx].token
                failed_tokens.append(failed_token)

                logger.error(
                    "Failed to send notification to device",
                    extra={
                        "firebase_token": failed_token,
                    },
                )
        self.failed_token_count = len(failed_tokens)

    @property
    def _response_data(self):
        return dict(
            total_device_count=self.total_device_count,
            total_token_count=self.total_token_count,
            total_enabled_count=self.total_enabled_count,
            failed_token_count=self.failed_token_count,
        )
