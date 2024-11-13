import logging

import requests
from django.conf import settings
from django.utils import timezone

from construction_work.models import WarningMessage

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Something went wrong calling the notification service"""


def call_notification_service(warning: WarningMessage) -> tuple[int, dict]:
    """Send a notification for a warning message to registered devices.

    Args:
        warning: The warning message to send notification for

    Returns:
        Tuple of (status_code, response_data) from notification service

    Raises:
        NotificationServiceError: If the notification service request fails
    """
    client_ids = list(
        warning.project.device_set.exclude(device_id=None).values_list(
            "device_id", flat=True
        )
    )

    request_data = {
        "title": warning.title,
        "body": warning.body,
        "module_slug": "construction-work",
        "context": {
            "linkSourceid": str(warning.pk),
            "type": "ProjectWarningCreatedByProjectManager",
        },
        "created_at": timezone.now().isoformat(),
        "client_ids": client_ids,
    }

    api_url = settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"]

    try:
        response = requests.post(api_url, json=request_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(
            "Failed to post notification",
            extra={
                "error": str(e),
                "warning_id": warning.pk,
            },
        )
        raise NotificationServiceError("Failed to post notification") from e

    warning.notification_sent = True
    warning.save()

    return response.status_code, response.json()
