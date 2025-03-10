from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.utils.image_utils import get_example_image_file
from image.models import ImageSet, ImageVariant


class ImageSetCreateViewTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("image-create-imageset")

    @override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
    def test_create_imageset_success_jpg(self):
        file = get_example_image_file("core/tests/example.jpg")
        self._create_imageset_success(file)

    @override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
    def test_create_imageset_success_heic(self):
        file = get_example_image_file("core/tests/example.heic")
        self._create_imageset_success(file)

    def _create_imageset_success(self, file: SimpleUploadedFile):
        payload = {"description": "Test", "image": file}
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertIn("variants", response.data)
        self.assertIn("description", response.data)

    def test_create_imageset_missing_image(self):
        response = self.client.post(
            self.url, {"description": "Test"}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)

    def test_create_imageset_invalid_file(self):
        payload = {"description": "Invalid file", "image": "not_an_image"}
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)


@override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
class ImageSetDetailViewTests(APITestCase):
    def setUp(self):
        self.headers = {settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]}
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
        response = self.client.get(self.url, headers=self.headers)
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
        response = self.client.delete(self.url, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ImageSet.objects.filter(pk=self.image_set_id).exists())

        # Check if variants and stored images are deleted
        variant_count = ImageVariant.objects.count()
        self.assertEqual(0, variant_count)
        self.assertFalse(default_storage.exists(self.image_variant_name))
