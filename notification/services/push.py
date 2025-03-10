import copy
import json
import logging

import firebase_admin
from django.conf import settings
from django.db.models import Exists, OuterRef
from firebase_admin import credentials, messaging

from core.services.image_set import ImageSetService
from notification.models import (
    Device,
    Notification,
    NotificationPushServiceEnabled,
    NotificationPushTypeEnabled,
)

logger = logging.getLogger(__name__)


class PushServiceDeviceLimitError(Exception):
    """Raise when too many devices were passed"""

    pass


class PushService:
    def __init__(
        self, source_notification: Notification, device_ids: list[str]
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

        max_devices = settings.FIREBASE_DEVICE_LIMIT
        if len(device_ids) > max_devices:
            raise PushServiceDeviceLimitError(
                f"Too many devices [{len(device_ids)=}, {max_devices=}]"
            )

        self.device_ids = device_ids
        self.source_notification = source_notification
        self.source_notification.id = None

    def push(self) -> dict:
        known_devices = (
            Device.objects.filter(
                external_id__in=self.device_ids,
            )
            .annotate(
                wants_notification=Exists(
                    NotificationPushTypeEnabled.objects.filter(
                        device=OuterRef("pk"),
                        notification_type=self.source_notification.notification_type,
                    )
                )
                & Exists(
                    NotificationPushServiceEnabled.objects.filter(
                        device=OuterRef("pk"),
                        service_name=self.source_notification.module_slug,
                    )
                )
            )
            .all()
        )

        known_device_ids = [device.external_id for device in known_devices]
        unknown_device_ids = set(self.device_ids) - set(known_device_ids)
        new_devices = Device.objects.bulk_create(
            Device(external_id=device_id) for device_id in unknown_device_ids
        )

        all_devices = list(known_devices) + new_devices
        notifications = self.create_notifications(all_devices)

        response_data = self.push_messages(notifications, known_devices)

        # NOTE: we're not yet checking if the device has the notification type enabled
        # TODO: when this gets activated, unit tests need to be added!

        # known_devices_with_notification_enabled = [
        #     device for device in known_devices if device.wants_notification
        # ]
        # response_data = self.push_messages(
        #     notifications, known_devices_with_notification_enabled
        # )

        response_data["total_device_count"] = len(self.device_ids)
        response_data["unknown_device_count"] = len(unknown_device_ids)
        return response_data

    def create_notifications(self, devices: list[Device]) -> dict[str, Notification]:
        """
        The supplied source_notification will be duplicated for every device.

        Returns:
            list[Notification]: newly created notification objects
        """
        new_notifications = {}
        for c in devices:
            new_notification: Notification = copy.copy(self.source_notification)
            new_notification.device = c
            new_notifications[c.external_id] = new_notification

        Notification.objects.bulk_create(new_notifications.values())
        return new_notifications

    def push_messages(self, notifications: dict[str, Notification], devices) -> dict:
        """
        Forwards notification to Firebase, to be pushed to devices.

        If device has a firebase token, a Firebase message will be crafted
        and finally send as a batch to Firebase.

        Args:
            notifications (list[Notification]): notifications used for Firebase message data
        """

        devices_with_token = [c for c in devices if c.firebase_token]
        if not devices_with_token:
            logger.info(
                "Notification(s) created, but none of the devices have a Firebase token",
                extra={
                    "total_device_count": len(self.device_ids),
                },
            )
            return {
                "devices_with_token_count": 0,
                "failed_token_count": 0,
            }

        firebase_messages = []
        for device in devices_with_token:
            notification_obj = notifications[device.external_id]
            message = self._define_firebase_message(device, notification_obj)
            firebase_messages.append(message)
        batch_response = messaging.send_each(firebase_messages)

        failed_tokens = []
        if batch_response.failure_count > 0:
            failed_tokens = self._log_failures(batch_response, firebase_messages)

        return {
            "devices_with_token_count": len(devices_with_token),
            "failed_token_count": len(failed_tokens),
        }

    def _define_firebase_message(
        self, device: Device, notification_obj: Notification
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
            token=device.firebase_token,
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

    def _log_failures(
        self, batch_response, firebase_messages: list[messaging.Message]
    ) -> list[str]:
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
        return failed_tokens
