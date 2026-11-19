import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock, patch

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from requests import HTTPError
from rest_framework import status
from rest_framework.test import APIClient

from core.authentication import APIKeyAuthentication
from core.tests.test_authentication import BasicAPITestCase
from core.utils.image_utils import (
    EXAMPLE_HEIC_FILE,
    EXAMPLE_JPG_FILE,
    get_example_image_data,
    get_example_image_file,
)
from image.models import ImageSet, ImageVariant


class ImageSetCreateViewTests(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("image-create-imageset")

    def test_create_imageset_success_jpg(self):
        file = get_example_image_file(EXAMPLE_JPG_FILE)
        self._create_imageset_success(file)

    def test_create_imageset_success_heic(self):
        file = get_example_image_file(EXAMPLE_HEIC_FILE)
        self._create_imageset_success(file)

    def _create_imageset_success(self, file: SimpleUploadedFile):
        payload = {"description": "Test", "image": file}
        response = self.client.post(
            self.url, payload, format="multipart", headers=self.api_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertIn("variants", response.data)
        self.assertIn("description", response.data)

    def test_create_imageset_missing_image(self):
        response = self.client.post(
            self.url,
            {"description": "Test"},
            format="multipart",
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)

    def test_create_imageset_invalid_file(self):
        payload = {"description": "Invalid file", "image": "not_an_image"}
        response = self.client.post(
            self.url, payload, format="multipart", headers=self.api_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)

    def test_create_imageset_without_identifier_twice(self):
        """
        Test that imageset without identifier can be created twice.
        There is a unique constraint on the identifier field,
        but this constraint is only applied to a non-null identifier field.
        """

        def post_imageset():
            payload = {
                "description": "test",
                "image": get_example_image_file(EXAMPLE_JPG_FILE),
            }
            return self.client.post(
                self.url, payload, format="multipart", headers=self.api_headers
            )

        response = post_imageset()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        image_set = ImageSet.objects.get(pk=response.data["id"])
        self.assertIsNone(image_set.identifier)

        response = post_imageset()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        image_set = ImageSet.objects.get(pk=response.data["id"])
        self.assertIsNone(image_set.identifier)

    def test_create_imageset_with_same_identifier_twice(self):
        """
        Test that imageset with the same identifier can not be created twice.
        There is a unique constraint on the identifier field,
        that applies to a non-null identifier field.
        """

        def post_imageset():
            payload = {
                "description": "test",
                "image": get_example_image_file(EXAMPLE_JPG_FILE),
                "identifier": "foobar",
            }
            return self.client.post(
                self.url, payload, format="multipart", headers=self.api_headers
            )

        response = post_imageset()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = post_imageset()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(
            response,
            "Er bestaat al een image set met eenzelfde identifier.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ImageSetFromUrlCreateViewTests(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("image-create-imageset-from-url")

    @patch("image.serializers.requests.get")
    def test_create_imageset_from_url_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = get_example_image_data()

        payload = {"url": "https://example.com/image.jpg"}
        response = self.client.post(self.url, payload, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertIn("variants", response.data)
        url_hash = hashlib.sha256(payload["url"].encode("utf-8")).hexdigest()
        self.assertEqual(response.data["identifier"], url_hash)

    @patch("image.serializers.requests.get")
    def test_get_imageset_when_url_hash_exists(self, mock_get):
        payload = {"url": "https://example.com/image.jpg"}
        url_hash = hashlib.sha256(payload["url"].encode("utf-8")).hexdigest()
        image_variant = ImageVariant.objects.create(image=get_example_image_file())
        image_set = ImageSet.objects.create(
            identifier=url_hash,
            image_small=image_variant,
            image_medium=image_variant,
            image_large=image_variant,
        )

        response = self.client.post(self.url, payload, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], image_set.id)
        self.assertEqual(response.data["identifier"], url_hash)
        mock_get.assert_not_called()

    @patch("image.serializers.requests.get")
    def test_repeated_url_request_reuses_imageset_without_fetching_again(
        self, mock_get
    ):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = get_example_image_data()
        payload = {"url": "https://example.com/image.jpg"}

        first_response = self.client.post(self.url, payload, headers=self.api_headers)
        second_response = self.client.post(self.url, payload, headers=self.api_headers)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(first_response.data["id"], second_response.data["id"])
        self.assertEqual(ImageSet.objects.count(), 1)
        mock_get.assert_called_once()

    @patch("image.serializers.requests.get")
    def test_different_urls_create_distinct_imagesets(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = get_example_image_data()
        urls = [
            "https://example.com/first.jpg",
            "https://example.com/second.jpg",
        ]

        responses = [
            self.client.post(self.url, {"url": url}, headers=self.api_headers)
            for url in urls
        ]

        self.assertEqual([response.status_code for response in responses], [200, 200])
        self.assertNotEqual(responses[0].data["id"], responses[1].data["id"])
        self.assertEqual(
            [response.data["identifier"] for response in responses],
            [hashlib.sha256(url.encode("utf-8")).hexdigest() for url in urls],
        )
        self.assertEqual(ImageSet.objects.count(), 2)

    def test_create_imageset_from_url_invalid_url(self):
        def assert_invalid_url(url):
            payload = {"url": url}
            response = self.client.post(self.url, payload, headers=self.api_headers)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        assert_invalid_url("not_a_url")
        assert_invalid_url("http://")
        assert_invalid_url("http://.com")
        assert_invalid_url("http://com")
        assert_invalid_url("http://.com/")
        assert_invalid_url("http://.com/image")
        assert_invalid_url("http://.com/image.jpg")

    @patch("image.serializers.requests.get")
    def test_create_imageset_from_url_invalid_image(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"not_an_image"
        payload = {"url": "https://example.com/image.jpg"}
        response = self.client.post(self.url, payload, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("image.serializers.requests.get")
    def test_create_imageset_from_url_unreachable(self, mock_get):
        mock_get.side_effect = HTTPError("Unreachable URL")
        payload = {"url": "https://example.com/image.jpg"}
        response = self.client.post(self.url, payload, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
)
class ImageSetFromUrlCreateConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.url = reverse("image-create-imageset-from-url")
        authentication = APIKeyAuthentication()
        self.headers = {authentication.api_key_header: authentication.api_keys[0]}

    @patch("image.serializers.requests.get")
    def test_concurrent_requests_for_same_url_reuse_imageset(self, mock_get):
        url = "https://example.com/image.jpg"
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        fetch_barrier = Barrier(2)

        def fetch_image(*args, **kwargs):
            fetch_barrier.wait(timeout=10)
            response = Mock(status_code=200, content=get_example_image_data())
            return response

        mock_get.side_effect = fetch_image

        def post_image():
            close_old_connections()
            try:
                client = APIClient()
                return client.post(self.url, {"url": url}, headers=self.headers)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(lambda _: post_image(), range(2)))

        self.assertEqual([response.status_code for response in responses], [200, 200])
        self.assertEqual(responses[0].data["id"], responses[1].data["id"])
        self.assertEqual(ImageSet.objects.filter(identifier=url_hash).count(), 1)
        self.assertEqual(ImageVariant.objects.count(), 3)
        self.assertEqual(len(default_storage.listdir("image")[1]), 3)


class ImageSetDetailViewTests(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        file = get_example_image_file()
        variant_1 = ImageVariant.objects.create(image=file)
        variant_2 = ImageVariant.objects.create(image=file)
        variant_3 = ImageVariant.objects.create(image=file)
        self.image_variant_name = variant_1.image.name
        self.image_set = ImageSet.objects.create(
            description="Test Image Set",
            image_small=variant_1,
            image_medium=variant_2,
            image_large=variant_3,
        )
        self.image_set_id = self.image_set.id
        self.url = reverse("image-detail-imageset", kwargs={"pk": self.image_set_id})

    def test_get_imageset(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.image_set_id)
        self.assertEqual(response.data["description"], "Test Image Set")
        self.assertEqual(len(response.data["variants"]), 3)

    def test_delete_imageset(self):
        # Check if variants and stored images can be found
        self.assertTrue(default_storage.exists(self.image_variant_name))
        variant_count = ImageVariant.objects.count()
        self.assertEqual(3, variant_count)

        # Delete image set
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ImageSet.objects.filter(pk=self.image_set_id).exists())

        # Check if variants and stored images are deleted
        variant_count = ImageVariant.objects.count()
        self.assertEqual(0, variant_count)
        self.assertFalse(default_storage.exists(self.image_variant_name))
