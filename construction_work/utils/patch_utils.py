import uuid
from unittest.mock import MagicMock

import requests
from django.utils import timezone

from core.utils.patch_utils import create_jwt_token


def create_bearer_token(*args, **kwargs):
    return f"Bearer {create_jwt_token(*args, **kwargs)}"


class MockNotificationResponse:
    def __init__(self, title, body, warning_id=1, status_code=200):
        self.warning_id = warning_id
        self.title = title
        self.body = body
        self.status_code = status_code

    def get_response(self):
        mock_response = MagicMock()
        mock_response.json = self.json
        mock_response.status_code = self.status_code
        mock_response.raise_for_status = self.raise_for_status
        return mock_response

    def json(self):
        return {
            "push_message": {
                "title": self.title,
                "body": self.body,
                "module_slug": "construction-work",
                "context": {
                    "linkSourceid": self.warning_id,
                    "type": "ProjectWarningCreatedByProjectManager",
                    "notificationId": str(uuid.uuid4()),
                },
                "created_at": timezone.now().isoformat(),
                "is_read": False,
            }
        }

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.exceptions.HTTPError(f"{self.status_code} Error")
