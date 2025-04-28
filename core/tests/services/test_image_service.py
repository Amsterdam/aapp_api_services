from unittest.mock import patch

import requests
from django.conf import settings
from django.test import TestCase

from core.services.image_set import ImageSetService

EXAMPLE_RESPONSE = {
    "id": 12,
    "description": "test",
    "variants": [
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/small.JPEG",
            "width": 320,
            "height": 180,
        },
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/medium.JPEG",
            "width": 768,
            "height": 432,
        },
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/large.JPEG",
            "width": 1280,
            "height": 720,
        },
    ],
}


@patch("core.services.image_set.requests.get")
class TestImageService(TestCase):
    def test_init(self, mock_requests):
        image_service = ImageSetService()
        image_service.get(1)
        mock_requests.assert_called_with(
            "http://api-image:8000/internal/api/v1/image/1",
            headers={settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]},
        )

    def test_url_small(self, mock_requests):
        image_service = ImageSetService()
        image_service.get(1)
        image_service.data = EXAMPLE_RESPONSE
        assert (
            image_service.url_small
            == "https://ontw.app.amsterdam.nl/media/image/small.JPEG"
        )

    def test_url_medium(self, mock_requests):
        image_service = ImageSetService()
        image_service.get(1)
        image_service.data = EXAMPLE_RESPONSE
        assert (
            image_service.url_medium
            == "https://ontw.app.amsterdam.nl/media/image/medium.JPEG"
        )

    def test_url_large(self, mock_requests):
        image_service = ImageSetService()
        image_service.get(1)
        image_service.data = EXAMPLE_RESPONSE
        assert (
            image_service.url_large
            == "https://ontw.app.amsterdam.nl/media/image/large.JPEG"
        )

    def test_json(self, mock_requests):
        image_service = ImageSetService()
        image_service.get(1)
        image_service.data = EXAMPLE_RESPONSE
        assert image_service.json() == EXAMPLE_RESPONSE

    def test_exists(self, mock_requests):
        mock_requests.status_code = 200
        image_service = ImageSetService()
        assert image_service.exists(1)

    def test_exists_not_found(self, mock_requests):
        mock_requests.side_effect = requests.HTTPError()
        image_service = ImageSetService()
        assert not image_service.exists(1)

    @patch("core.services.image_set.requests.post")
    def test_upload(self, mock_requests_post, _):
        mock_requests_post.status_code = 200
        image_service = ImageSetService()
        image = b"test"
        description = "test"
        image_service.upload(image=image, description=description)

        mock_requests_post.assert_called_with(
            settings.IMAGE_ENDPOINTS["POST_IMAGE"],
            headers={settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]},
            data={"description": description},
            files={"image": image},
        )

    @patch("core.services.image_set.requests.post")
    def test_upload_no_description(self, mock_requests_post, _):
        mock_requests_post.status_code = 200
        image_service = ImageSetService()
        image = b"test"
        image_service.upload(image=image)

        mock_requests_post.assert_called_with(
            settings.IMAGE_ENDPOINTS["POST_IMAGE"],
            headers={settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]},
            data={},
            files={"image": image},
        )
