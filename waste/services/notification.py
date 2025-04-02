import logging

import requests
from django.conf import settings
from django.utils import timezone

from core.enums import Module, NotificationType

logger = logging.getLogger(__name__)


def call_notification_service(device_ids: list[str], type: str) -> tuple[int, dict]:
    """Send a notification for a warning message to registered devices.

    Args:
        warning: The warning message to send notification for
        image: The image to send with the notification

    Returns:
        Tuple of (status_code, response_data) from notification service

    Raises:
        NotificationServiceError: If the notification service request fails
    """

    request_data = get_request_data(device_ids, type)
    api_url = settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"]
    response = requests.post(api_url, json=request_data)
    response.raise_for_status()
    return response.status_code, response.json()


def get_request_data(device_ids, type):
    request_data = {
        "title": f"Morgen wordt je {type} afval opgehaald",
        "body": "Denk er aan om je container buiten te zetten",
        "module_slug": Module.WASTE.value,
        "context": {
            "linkSourceid": type,
            "type": "WasteDateReminder",
            "module_slug": Module.WASTE.value,
        },
        "created_at": timezone.now().isoformat(),
        "device_ids": device_ids,
        "notification_type": NotificationType.WASTE_DATE_REMINDER.value,
    }
    return request_data
