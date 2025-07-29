import logging
from typing import NamedTuple

import requests
from django.conf import settings
from django.utils import timezone

from core.enums import Module, NotificationType

logger = logging.getLogger(__name__)


class InternalServiceError(Exception):
    """Something went wrong calling the notification service"""


class NotificationData(NamedTuple):
    link_source_id: str
    title: str
    message: str
    device_ids: list[str]
    image_set_id: int = None


class AbstractNotificationService:
    module_slug: Module = None
    notification_type: NotificationType = None
    post_notification_url = settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"]

    def __init__(self):
        self.link_source_id = None

    def send(self, *args, **kwargs):
        """
        Send a notification to users based on the provided notification data.
        This method should be overridden by subclasses to implement specific notification logic.
        The 'process' method should be called with the notification data.
        """
        raise NotImplementedError(
            "Subclasses must implement the send method to process notifications."
        )

    def process(
        self,
        notification: NotificationData,
    ):
        """
        Send notifications to users based on the notification type and budget codes.
        """
        self.link_source_id = notification.link_source_id
        request_data = self.get_request_data(notification)

        self.make_post_request(request_data)

    def get_request_data(
        self,
        notification: NotificationData,
    ) -> dict:
        request_data = {
            "title": notification.title,
            "body": notification.message,
            "module_slug": self.module_slug,
            "notification_type": self.notification_type,
            "created_at": timezone.now().isoformat(),
            "context": self.get_context(),
            "device_ids": notification.device_ids,
        }
        if notification.image_set_id:
            request_data["image"] = notification.image_set_id
        return request_data

    def get_context(self) -> dict:
        return {
            "linkSourceid": self.link_source_id,
            "type": self.notification_type,
            "module_slug": self.module_slug,
        }

    def make_post_request(self, request_data=None) -> requests.Response:
        try:
            headers = {
                settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0],
            }
            response = requests.post(
                self.post_notification_url,
                json=request_data,
                headers=headers,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(
                "Failed to make post request",
                extra={
                    "error": str(e),
                    "link_source_id": self.link_source_id,
                    "api_url": self.post_notification_url,
                },
            )
            error_message = "Failed posting notification"
            raise InternalServiceError(error_message) from e
