import logging

import requests
from django.conf import settings
from django.utils import timezone

from city_pass.models import Notification, Session
from core.enums import Module, NotificationType

logger = logging.getLogger(__name__)

POST_NOTIFICATION_URL = settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"]


class InternalServiceError(Exception):
    """Something went wrong calling the notification service"""


class NotificationService:
    module_slug = Module.CITY_PASS.value
    notification_type = NotificationType.CITY_PASS_NOTIFICATION.value

    def __init__(self):
        self.post_notification_url = settings.NOTIFICATION_ENDPOINTS[
            "INIT_NOTIFICATION"
        ]
        self.device_ids = None

    def set_device_ids(self, notification: Notification):
        budgets = list(notification.budgets.all())
        if budgets:
            sessions = Session.objects.filter(passdata__budgets__in=budgets)
        else:
            sessions = Session.objects.all()
        device_ids = (
            sessions.exclude(device_id=None)
            .values_list("device_id", flat=True)
            .distinct()
        )
        self.device_ids = list(device_ids)

    def send(self, notification: Notification):
        """
        Send notifications to users based on the notification type and budget codes.

        Args:
            notification (Notification): The notification instance to process.
        """
        if self.device_ids is None:
            self.set_device_ids(notification)

        request_data = self.create_request_data(notification)
        self.make_post_request(
            notification_pk=notification.pk, request_data=request_data
        )

        notification.send_at = timezone.now()
        notification.nr_sessions = len(self.device_ids)
        notification.save()

    def create_request_data(self, notification: Notification) -> dict:
        request_data = {
            "title": notification.title,
            "body": notification.message,
            "module_slug": self.module_slug,
            "notification_type": self.notification_type,
            "created_at": timezone.now().isoformat(),
            "context": {
                "linkSourceid": str(notification.pk),
                "type": self.notification_type,
                "module_slug": self.module_slug,
            },
            "device_ids": self.device_ids,
        }
        if notification.image_set_id:
            request_data["image"] = notification.image_set_id
        return request_data

    def make_post_request(
        self, notification_pk: int, request_data=None, files=None
    ) -> requests.Response:
        try:
            headers = {
                settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0],
            }
            response = requests.post(
                self.post_notification_url,
                json=request_data,
                files=files,
                headers=headers,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(
                "Failed to make post request",
                extra={
                    "error": str(e),
                    "notification_pk": notification_pk,
                    "api_url": self.post_notification_url,
                },
            )
            error_message = "Failed calling internal service"
            raise InternalServiceError(error_message) from e
