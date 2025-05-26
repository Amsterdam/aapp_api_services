import responses
from django.conf import settings
from django.core.cache import cache

from core.services.image_set import ImageSetService
from core.tests.test_authentication import ResponsesActivatedAPITestCase

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


class TestImageService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.rsp_get = responses.get(
            f"{settings.IMAGE_ENDPOINTS['DETAIL']}/1", json=EXAMPLE_RESPONSE
        )
        self.rsp_post = responses.post(
            settings.IMAGE_ENDPOINTS["POST_IMAGE"], json=EXAMPLE_RESPONSE
        )
        self.rsp_post_from_url = responses.post(
            settings.IMAGE_ENDPOINTS["POST_IMAGE_FROM_URL"], json=EXAMPLE_RESPONSE
        )

    def test_init(self):
        image_service = ImageSetService()
        image_service.get(1)
        self.assertEquals(self.rsp_get.call_count, 1)

    def test_url_small(self):
        image_service = ImageSetService()
        image_service.get(1)
        self.assertEquals(
            image_service.url_small,
            "https://ontw.app.amsterdam.nl/media/image/small.JPEG",
        )

    def test_url_medium(self):
        image_service = ImageSetService()
        image_service.get(1)
        self.assertEqual(
            image_service.url_medium,
            "https://ontw.app.amsterdam.nl/media/image/medium.JPEG",
        )

    def test_url_large(self):
        image_service = ImageSetService()
        image_service.get(1)
        self.assertEqual(
            image_service.url_large,
            "https://ontw.app.amsterdam.nl/media/image/large.JPEG",
        )

    def test_json(self):
        image_service = ImageSetService()
        image_service.get(1)
        self.assertEqual(image_service.json(), EXAMPLE_RESPONSE)

    def test_exists(self):
        image_service = ImageSetService()
        self.assertTrue(image_service.exists(1))
        self.assertEqual(self.rsp_get.call_count, 1)

        cached_image = cache.get("core.services.image_set.get_from_id.1")
        self.assertIsNotNone(cached_image)
        self.assertEqual(cached_image, EXAMPLE_RESPONSE)

    def test_exists_not_found(self):
        responses.reset()
        responses.get(f"{settings.IMAGE_ENDPOINTS['DETAIL']}/1", status=404)
        image_service = ImageSetService()
        self.assertFalse(image_service.exists(1))

    def test_upload(self):
        image_service = ImageSetService()
        image = b"test"
        description = "test"
        image_service.upload(image=image, description=description)

        self.assertEqual(self.rsp_post.call_count, 1)

    def test_upload_no_description(self):
        image_service = ImageSetService()
        image = b"test"
        image_service.upload(image=image)

        self.assertEqual(self.rsp_post.call_count, 1)

    def test_upload_from_url(self):
        image_service = ImageSetService()
        image_service.get_or_upload_from_url("https://example.com/image.jpg")

        self.assertEqual(self.rsp_post_from_url.call_count, 1)
