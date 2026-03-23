import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings
from firebase_admin import messaging

from core.services.image_set import ImageSetService
from notification.models import Notification

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=settings.MAX_FIREBASE_WORKERS)


class PushService:
    def push(self, notifications: list[Notification]) -> int:
        """
        Forwards notification to Firebase, to be pushed to devices.

        Processes notifications in batches of 5000 to avoid high memory usage.
        Each batch is sent concurrently using a thread pool.

        Args:
            notifications (list[Notification]): notifications used for Firebase message data
        """
        failed_token_count = 0
        for batch in self._batch_messages(notifications):
            firebase_messages = [self._define_firebase_message(n) for n in batch]
            futures = []
            for msg in firebase_messages:
                futures.append(thread_pool.submit(self._send_message, msg))

            for future in as_completed(futures):
                result = future.result()
                if result is False:
                    failed_token_count += 1
        return failed_token_count

    def _send_message(self, message: messaging.Message) -> bool:
        try:
            messaging.send(message)
            return True
        except Exception:
            logger.error(
                "Failed to send notification to device",
                extra={"firebase_token": getattr(message, "token", None)},
            )
            return False

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

    def _batch_messages(
        self, notifications: list[Notification]
    ) -> list[list[Notification]]:
        """
        Split the device list into batches to prevent memory overflow.
        """
        max_devices = 5000
        batches = [
            notifications[i : i + max_devices]
            for i in range(0, len(notifications), max_devices)
        ]
        return batches
