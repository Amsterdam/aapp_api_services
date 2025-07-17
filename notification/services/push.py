import json
import logging

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

from core.services.image_set import ImageSetService
from notification.models import Notification

logger = logging.getLogger(__name__)


class PushService:
    def __init__(self) -> None:
        """
        First the Firebase admin will be initialized.
        Firebase manages its own connections, so when multiple services are initialized,
        Firebase will check if there is already an active connection setup.
        """
        if not firebase_admin._apps:
            creds = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
            firebase_admin.initialize_app(creds)
        else:
            firebase_admin.get_app()

    def push(self, notifications: list[Notification]) -> int:
        """
        Forwards notification to Firebase, to be pushed to devices.

        If device has a firebase token, a Firebase message will be crafted
        and finally send as a batch to Firebase.

        Args:
            notifications (list[Notification]): notifications used for Firebase message data
        """

        firebase_messages = [self._define_firebase_message(n) for n in notifications]
        firebase_batches = self._batch_messages(firebase_messages)
        failed_token_count = 0
        for batch in firebase_batches:
            batch_response = messaging.send_each(batch)
            if batch_response.failure_count > 0:
                failed_token_count += batch_response.failure_count
                self._log_failures(batch_response, firebase_messages)
        return failed_token_count

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

    def _batch_messages(self, messages) -> list[list[messaging.Message]]:
        """
        Split the device list into batches of settings.MAX_DEVICES_PER_REQUEST devices.
        """
        max_devices = settings.MAX_DEVICES_PER_REQUEST
        batches = [
            messages[i : i + max_devices] for i in range(0, len(messages), max_devices)
        ]
        return batches

    def _log_failures(self, batch_response, firebase_messages: list[messaging.Message]):
        responses = batch_response.responses
        for idx, resp in enumerate(responses):
            if not resp.success:
                failed_token = firebase_messages[idx].token
                logger.error(
                    "Failed to send notification to device",
                    extra={"firebase_token": failed_token},
                )
