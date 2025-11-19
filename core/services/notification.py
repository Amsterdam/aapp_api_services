import logging
import uuid
from datetime import datetime
from typing import NamedTuple

import requests
from django.conf import settings
from django.utils import timezone

from core.enums import Module, NotificationType
from core.services.internal_http_client import InternalServiceSession

logger = logging.getLogger(__name__)


class InternalServiceError(Exception):
    """Something went wrong calling the notification service"""


class NotificationData(NamedTuple):
    link_source_id: str
    title: str
    message: str
    device_ids: list[str]
    image_set_id: int = None
    make_push: bool = True


class AbstractNotificationService:
    module_slug: Module = None
    notification_type: NotificationType = None

    def __init__(self):
        self.client = InternalServiceSession()
        self.link_source_id = None
        self.post_scheduled_notification_url = settings.NOTIFICATION_ENDPOINTS[
            "SCHEDULED_NOTIFICATION"
        ]
        self.last_notification_url = settings.NOTIFICATION_ENDPOINTS["LAST_TIMESTAMP"]
        self.notifications_url = settings.NOTIFICATION_ENDPOINTS["NOTIFICATIONS"]

    def get_last_timestamp(self, device_id: str) -> datetime | None:
        headers = {"DeviceId": device_id}
        response = self.make_request(
            self.last_notification_url,
            method="GET",
            params={"module_slug": self.module_slug},
            additional_headers=headers,
        )
        timestamps = [
            datetime.fromisoformat(scope["last_create"])
            for scope in response
            if scope["last_create"] is not None
        ]
        return max(timestamps) if timestamps else None

    def get_notifications(self, device_id: str) -> list[dict]:
        headers = {
            "DeviceId": device_id,
        }
        response = self.make_request(
            self.notifications_url, method="GET", additional_headers=headers
        )
        return response

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
        expiry_minutes: int = 15,
    ):
        """
        Send notifications to users based on the notification type and budget codes.
        """
        self.link_source_id = notification.link_source_id
        request_data = self.get_request_data(
            notification, expiry_minutes=expiry_minutes
        )

        self.make_request(
            self.post_scheduled_notification_url,
            method="POST",
            request_data=request_data,
        )

    def get_request_data(
        self,
        notification: NotificationData,
        expiry_minutes: int,
    ) -> dict:
        now = timezone.now() + timezone.timedelta(seconds=5)
        request_data = {
            "title": notification.title,
            "body": notification.message,
            "module_slug": self.module_slug,
            "notification_type": self.notification_type,
            "created_at": timezone.now().isoformat(),
            "context": self.get_context(),
            "device_ids": notification.device_ids,
            "make_push": notification.make_push,
            "scheduled_for": now.isoformat(),
            "expires_at": (
                now + timezone.timedelta(minutes=expiry_minutes)
            ).isoformat(),
            "identifier": f"{self.module_slug}_{uuid.uuid4()}",
        }
        if notification.image_set_id:
            request_data["image"] = notification.image_set_id
        return request_data

    def get_context(self) -> dict:
        """Context can only contain string values!"""
        return {
            "linkSourceid": str(self.link_source_id),
            "type": self.notification_type,
            "module_slug": self.module_slug,
        }

    def make_request(
        self, url, method, request_data=None, additional_headers=None, params=None
    ):
        try:
            response = self.client.request(
                method,
                url=url,
                json=request_data,
                headers=additional_headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                "Failed to make request",
                extra={
                    "error": str(e),
                    "link_source_id": self.link_source_id,
                    "api_url": url,
                },
            )
            error_message = f"Failed notification service {method} request"
            raise InternalServiceError(error_message) from e
