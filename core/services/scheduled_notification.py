import datetime
import logging
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Exception raised for errors calling the Notification Service."""

    pass


class ScheduledNotificationService:
    @property
    def _headers(self):
        return {
            settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0],
        }

    def add(
        self,
        title: str,
        body: str,
        scheduled_for: datetime,
        identifier: str,
        context: dict,
        device_ids: list[str],
        notification_type: str,
        module_slug: str = None,
        image: str = None,
        expires_at: datetime = None,
    ):
        request_data = {
            "title": title,
            "body": body,
            "scheduled_for": scheduled_for.isoformat(),
            "context": context,
            "identifier": identifier,
            "device_ids": device_ids,
            "notification_type": notification_type,
            "module_slug": module_slug or settings.SERVICE_NAME,
            "created_at": timezone.now().isoformat(),
        }
        if image:
            request_data["image"] = image
        if expires_at:
            request_data["expires_at"] = expires_at.isoformat()

        try:
            url = settings.NOTIFICATION_ENDPOINTS["SCHEDULED_NOTIFICATION"]
            response = requests.post(
                url,
                json=request_data,
                headers=self._headers,
            )
            response.raise_for_status()
        except Exception as e:
            raise NotificationServiceError(
                "Failed to create scheduled notification"
            ) from e
        return response.json()

    def get_all(self):
        try:
            url = settings.NOTIFICATION_ENDPOINTS["SCHEDULED_NOTIFICATION"]
            response = requests.get(
                url,
                headers=self._headers,
            )
            response.raise_for_status()
        except Exception as e:
            raise NotificationServiceError(
                "Failed to collect scheduled notifications"
            ) from e
        return response.json()

    def get(self, identifier: str):
        try:
            url = self._build_url(identifier)
            response = requests.get(
                url,
                headers=self._headers,
            )
            if response.status_code == 204:
                return None
            response.raise_for_status()
        except Exception as e:
            raise NotificationServiceError(
                "Failed to get scheduled notification"
            ) from e

        return response.json()

    def update(
        self,
        identifier: str,
        scheduled_for: datetime,
        device_ids: list[str],
    ):
        try:
            url = self._build_url(identifier)
            response = requests.patch(
                url,
                json={
                    "scheduled_for": scheduled_for.isoformat(),
                    "device_ids": device_ids,
                },
                headers=self._headers,
            )
            response.raise_for_status()
        except Exception as e:
            raise NotificationServiceError(
                "Failed to update scheduled notification"
            ) from e

        return response.json()

    def delete(self, identifier: str):
        try:
            url = self._build_url(identifier)
            response = requests.delete(
                url,
                headers=self._headers,
            )
            response.raise_for_status()
        except Exception as e:
            raise NotificationServiceError(
                "Failed to delete scheduled notification"
            ) from e

    def _build_url(self, identifier):
        return urljoin(
            f"{settings.NOTIFICATION_ENDPOINTS['SCHEDULED_NOTIFICATION']}/",
            identifier,
        )
