import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import firebase_admin.messaging as fam
import urllib3
from django.conf import settings
from firebase_admin import messaging

from core.services.image_set import ImageSetService
from notification.models import Notification

MAX_WORKERS = 50  # Match patched pool size
# Patch urllib3 connection pool size globally
urllib3.util.connection.HAS_IPV6 = False  # Avoid IPv6 issues
urllib3.connectionpool.ConnectionPool.DEFAULT_MAXSIZE = MAX_WORKERS
# Patch thread pool size for send_each globally
fam._THREAD_POOL_SIZE = MAX_WORKERS

logger = logging.getLogger(__name__)


class PushService:
    def push(self, notifications: list[Notification]) -> int:
        """
        Forwards notification to Firebase, to be pushed to devices.

        If device has a firebase token, a Firebase message will be crafted
        and finally sent as a batch to Firebase.

        Args:
            notifications (list[Notification]): notifications used for Firebase message data
        """

        firebase_messages = [self._define_firebase_message(n) for n in notifications]
        firebase_batches = self._batch_messages(firebase_messages)
        failed_token_count = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_batch = {
                executor.submit(messaging.send_each, batch): batch
                for batch in firebase_batches
            }
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    batch_response = future.result()
                    if batch_response.failure_count > 0:
                        failed_token_count += batch_response.failure_count
                        self._log_failures(batch_response, batch)
                except Exception as exc:
                    logger.error(f"Batch failed: {exc}")

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
