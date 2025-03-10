from unittest.mock import patch

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


@patch("requests.get")
class TestImageService(TestCase):
    def test_init(self, mock_requests):
        image_service = ImageSetService()
        image_service.get(1)
        mock_requests.assert_called_with(
            "http://api-image:8000/internal/api/v1/image/1"
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
