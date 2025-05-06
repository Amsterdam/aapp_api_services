import logging

import requests
from django.conf import settings
from django.utils import timezone

from construction_work.models.manage_models import WarningMessage
from core.enums import Module, NotificationType

logger = logging.getLogger(__name__)


class InternalServiceError(Exception):
    """Something went wrong calling the notification service"""


POST_NOTIFICATION_URL = settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"]
POST_IMAGE_URL = settings.IMAGE_ENDPOINTS["POST_IMAGE"]


def call_notification_service(warning: WarningMessage) -> tuple[int, dict]:
    """Send a notification for a warning message to registered devices.

    Args:
        warning: The warning message to send notification for
        image: The image to send with the notification

    Returns:
        Tuple of (status_code, response_data) from notification service

    Raises:
        NotificationServiceError: If the notification service request fails
    """
    warning_image = warning.warningimage_set.first()

    request_data = create_request_data(warning, warning_image)
    response = make_post_request(
        POST_NOTIFICATION_URL, warning_pk=warning.pk, request_data=request_data
    )

    warning.notification_sent = True
    warning.save()
    return response.status_code, response.json()


def create_request_data(warning: WarningMessage, warning_image) -> dict:
    device_ids = list(
        warning.project.device_set.exclude(device_id=None).values_list(
            "device_id", flat=True
        )
    )
    request_data = {
        "title": warning.project.title,
        "body": warning.title,
        "module_slug": Module.CONSTRUCTION_WORK.value,
        "context": {
            "linkSourceid": str(warning.pk),
            "type": "ProjectWarningCreatedByProjectManager",
            "module_slug": Module.CONSTRUCTION_WORK.value,
        },
        "created_at": timezone.now().isoformat(),
        "device_ids": device_ids,
        "notification_type": NotificationType.CONSTRUCTION_WORK_WARNING_MESSAGE.value,
    }
    if warning_image and warning_image.image_set_id:
        request_data["image"] = warning_image.image_set_id
    return request_data


def make_post_request(
    api_url: str, warning_pk: int, request_data=None, files=None
) -> requests.Response:
    try:
        headers = {
            settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0],
        }
        response = requests.post(
            api_url, json=request_data, files=files, headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(
            "Failed to make post request",
            extra={
                "error": str(e),
                "warning_id": warning_pk,
                "api_url": api_url,
            },
        )
        if api_url == POST_IMAGE_URL:
            error_message = "Failed posting image"
        elif api_url == POST_NOTIFICATION_URL:
            error_message = "Failed posting notification"
        else:
            error_message = "Failed calling internal service"
        raise InternalServiceError(error_message) from e

    return response
