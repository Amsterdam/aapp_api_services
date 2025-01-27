import logging

import requests
from django.conf import settings
from django.utils import timezone

from construction_work.models.manage_models import WarningMessage

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Something went wrong calling the notification service"""


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
    warning_pk = warning.pk
    image_id = get_image_id(warning)

    request_data = get_request_data(warning, image_id)
    api_url = settings.NOTIFICATION_ENDPOINTS["INIT_NOTIFICATION"]
    response = make_post_request(api_url, warning_pk, request_data=request_data)

    warning.notification_sent = True
    warning.save()
    return response.status_code, response.json()


def get_image_id(warning):
    if not warning.warningimage_set.exists():
        return None

    image_set = warning.warningimage_set.first()
    images = image_set.images.all()
    for image in images:
        if image.width == 1280:
            image_file = image.image.file
            break
    else:
        image_file = images[0].image.file

    api_url = settings.NOTIFICATION_ENDPOINTS["POST_IMAGE"]
    response = make_post_request(
        api_url, warning_pk=warning.pk, files={"image": image_file}
    )
    image_id = response.json()["id"]
    return image_id


def get_request_data(warning, image_id):
    device_ids = list(
        warning.project.device_set.exclude(device_id=None).values_list(
            "device_id", flat=True
        )
    )
    request_data = {
        "title": warning.project.title,
        "body": warning.title,
        "module_slug": settings.MODULE_SLUG,
        "context": {
            "linkSourceid": str(warning.pk),
            "type": "ProjectWarningCreatedByProjectManager",
        },
        "created_at": timezone.now().isoformat(),
        "device_ids": device_ids,
    }
    if image_id:
        request_data["image"] = image_id
    return request_data


def make_post_request(api_url, warning_pk, request_data=None, files=None):
    try:
        response = requests.post(api_url, json=request_data, files=files)
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
        raise NotificationServiceError("Failed to post image") from e

    return response
