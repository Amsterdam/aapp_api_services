from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from contact.models import NeighborhoodNotes, NeighborhoodNotesImage
from core.tests.test_authentication import BasicAPITestCase


class BaseNeighborhoodViewTestCase(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.device_id = "device-1"
        self.other_device_id = "device-2"
        self.base_headers = {**self.api_headers, "DeviceId": self.device_id}

        self.notes_url = reverse("neighborhood-notes-create-get")
        self.note_images_url = reverse("neighborhood-note-images")
        self.own_notes_url = reverse("neighborhood-notes-own")

    @staticmethod
    def _payload(response):
        data = response.json()
        if isinstance(data, list):
            return data
        return data.get("result", data)

    def _create_note(self, *, device_id=None, lat="52.370216", lng="4.895168"):
        return NeighborhoodNotes.objects.create(
            title="Test note",
            body="Body",
            contact_name="John",
            contact_number="0612345678",
            lat=lat,
            lng=lng,
            external_device_id=device_id or self.device_id,
        )


class TestNeighborhoodNoteImageUploadView(BaseNeighborhoodViewTestCase):
    @patch("contact.views.neighborhood_views.ImageSetService.upload")
    def test_upload_note_image_success(self, mock_upload):
        mock_upload.return_value = {
            "id": 999,
            "variants": [
                {
                    "image": "https://example.org/image-1.jpg",
                    "width": 640,
                    "height": 480,
                }
            ],
        }

        # Minimal valid 1x1 GIF bytes to satisfy Django image validation.
        image = SimpleUploadedFile(
            "test.gif",
            (
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
                b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00"
                b"\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )

        response = self.client.post(
            self.note_images_url,
            {"image": image, "description": "sample"},
            format="multipart",
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = self._payload(response)
        self.assertEqual(payload["image_set_id"], 999)


class TestCreateRetrieveNeighborhoodNoteView(BaseNeighborhoodViewTestCase):
    @patch("contact.serializers.neighborhood_serializers.ImageSetService.get")
    def test_create_note_with_images_success(self, mock_get):
        mock_get.return_value = {
            "id": 77,
            "variants": [
                {
                    "image": "https://example.org/image-1.jpg",
                    "width": 640,
                    "height": 480,
                },
                {
                    "image": "https://example.org/image-2.jpg",
                    "width": 320,
                    "height": 240,
                },
            ],
        }

        response = self.client.post(
            self.notes_url,
            {
                "title": "Created note",
                "body": "Created body",
                "contact_name": "Jane",
                "contact_number": "0611111111",
                "lat": "52.370216",
                "lng": "4.895168",
                "image_set_id": 77,
            },
            format="json",
            headers=self.base_headers,
        )

        self.assertEqual(response.status_code, 201)
        payload = self._payload(response)

        note = NeighborhoodNotes.objects.get(id=payload["note_id"])
        self.assertEqual(note.external_device_id, self.device_id)
        self.assertEqual(note.images.count(), 2)

    def test_get_notes_by_location_includes_images(self):
        in_range_note = self._create_note(lat="52.370216", lng="4.895168")
        NeighborhoodNotesImage.objects.create(
            note=in_range_note,
            foreign_id=1,
            uri="https://example.org/image-1.jpg",
            width=640,
            height=480,
        )

        self._create_note(
            device_id=self.other_device_id,
            lat="52.400000",
            lng="4.950000",
        )

        response = self.client.get(
            self.notes_url,
            {"lat": 52.370216, "lng": 4.895168},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = self._payload(response)

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], in_range_note.id)
        self.assertIn("images", payload[0])
        self.assertEqual(len(payload[0]["images"]), 1)
        self.assertEqual(
            payload[0]["images"][0]["uri"], "https://example.org/image-1.jpg"
        )


class TestDeleteNeighborhoodNoteView(BaseNeighborhoodViewTestCase):
    def test_delete_note_success_for_own_device(self):
        note = self._create_note(device_id=self.device_id)

        response = self.client.delete(
            reverse("neighborhood-notes-delete", kwargs={"note_id": note.id}),
            headers=self.base_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(NeighborhoodNotes.objects.filter(id=note.id).exists())

    def test_delete_note_not_found_for_other_device(self):
        note = self._create_note(device_id=self.other_device_id)

        response = self.client.delete(
            reverse("neighborhood-notes-delete", kwargs={"note_id": note.id}),
            headers=self.base_headers,
        )

        self.assertEqual(response.status_code, 404)


class TestRetrieveOwnNeighborhoodNotesView(BaseNeighborhoodViewTestCase):
    def test_get_own_notes_includes_images(self):
        own_note = self._create_note(device_id=self.device_id)
        NeighborhoodNotesImage.objects.create(
            note=own_note,
            foreign_id=2,
            uri="https://example.org/own-image.jpg",
            width=100,
            height=50,
        )
        self._create_note(device_id=self.other_device_id)

        response = self.client.get(self.own_notes_url, headers=self.base_headers)

        self.assertEqual(response.status_code, 200)
        payload = self._payload(response)

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], own_note.id)
        self.assertIn("images", payload[0])
        self.assertEqual(len(payload[0]["images"]), 1)
        self.assertEqual(
            payload[0]["images"][0]["uri"], "https://example.org/own-image.jpg"
        )
