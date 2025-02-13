import logging

import requests
from django.conf import settings
from django.utils import timezone

from construction_work.models.manage_models import WarningMessage

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
    image_id = get_image_id(warning)

    request_data = create_request_data(warning, image_id)
    response = make_post_request(
        POST_NOTIFICATION_URL, warning_pk=warning.pk, request_data=request_data
    )

    warning.notification_sent = True
    warning.save()
    return response.status_code, response.json()


def get_image_id(warning: WarningMessage) -> int | None:
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

    files_data = {"image": image_file}
    response = make_post_request(
        POST_IMAGE_URL, warning_pk=warning.pk, files=files_data
    )
    response_data = response.json()

    if "id" not in response_data:
        logger.error(
            "Image id not found in response",
            extra={
                "response_data": response_data,
                "warning_id": warning.pk,
                "api_url": POST_IMAGE_URL,
            },
        )
        raise InternalServiceError("Image id not found in response")
    image_id = response_data["id"]

    return image_id


def create_request_data(warning: WarningMessage, image_id: int | None) -> dict:
    device_ids = list(
        warning.project.device_set.exclude(device_id=None).values_list(
            "device_id", flat=True
        )
    )
    request_data = {
        "title": warning.project.title,
        "body": warning.title,
        "module_slug": settings.SERVICE_NAME,
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


def make_post_request(
    api_url: str, warning_pk: int, request_data=None, files=None
) -> requests.Response:
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
        if api_url == POST_IMAGE_URL:
            error_message = "Failed posting image"
        elif api_url == POST_NOTIFICATION_URL:
            error_message = "Failed posting notification"
        else:
            error_message = "Failed calling internal service"
        raise InternalServiceError(error_message) from e

    return response
