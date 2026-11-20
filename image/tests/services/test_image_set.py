import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest.mock import patch

import responses
from django.core.files.storage import default_storage
from django.db import IntegrityError, close_old_connections, connection
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from core.authentication import APIKeyAuthentication
from core.utils.image_utils import get_example_image_data, get_example_image_file
from image.models import ImageSet, ImageVariant
from image.services import image_set


class ImageSetServiceTests(TransactionTestCase):
    def setUp(self):
        self.enterContext(
            override_settings(
                STORAGES={
                    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}
                }
            )
        )
        self.remote_url = "https://example.com/image.jpg"
        self.identifier = hashlib.sha256(self.remote_url.encode()).hexdigest()
        authentication = APIKeyAuthentication()
        self.headers = {authentication.api_key_header: authentication.api_keys[0]}
        self.connection_ids = set()

    def post_image(self, route, description="test"):
        close_old_connections()
        try:
            connection.ensure_connection()
            self.connection_ids.add(connection.connection.info.backend_pid)
            payload = {"description": description}
            if route == "image-create-imageset-from-url":
                payload["url"] = self.remote_url
                request_format = "json"
            else:
                payload.update(
                    image=get_example_image_file(), identifier=self.identifier
                )
                request_format = "multipart"
            return APIClient().post(
                reverse(route), payload, format=request_format, headers=self.headers
            )
        finally:
            close_old_connections()

    def assert_only_winner_survives(self, winner):
        self.assertEqual(ImageSet.objects.count(), 1)
        self.assertEqual(ImageVariant.objects.count(), 3)
        image_set = ImageSet.objects.get()
        self.assertEqual(image_set.pk, winner.data["id"])
        self.assertEqual(image_set.identifier, self.identifier)
        expected_files = {
            variant.image.name.rsplit("/", 1)[1]
            for variant in ImageVariant.objects.all()
        }
        self.assertEqual(set(default_storage.listdir("image")[1]), expected_files)
        self.assertEqual(len(expected_files), 3)
        self.assertEqual(len(winner.data["variants"]), 3)

    @responses.activate
    def test_same_url_concurrent_requests_return_same_set(self):
        responses.get(self.remote_url, body=get_example_image_data())
        barrier = Barrier(2)
        create_from_url = image_set.create_from_url

        def synchronized_creation(*args, **kwargs):
            barrier.wait(timeout=10)
            return create_from_url(*args, **kwargs)

        with patch(
            "image.serializers.create_from_url", side_effect=synchronized_creation
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(self.post_image, "image-create-imageset-from-url")
                    for _ in range(2)
                ]
                results = [future.result(timeout=20) for future in futures]
        self.assertEqual([result.status_code for result in results], [200, 200])
        self.assertEqual(results[0].data, results[1].data)
        self.assertEqual(len(self.connection_ids), 2)
        self.assertEqual(len(responses.calls), 1)
        self.assert_only_winner_survives(results[0])

    @responses.activate
    def test_url_loser_returns_upload_winner_without_orphan_files(self):
        self.assert_cross_route_conflict(
            loser_route="image-create-imageset-from-url",
            winner_route="image-create-imageset",
            loser_status=200,
        )

    @responses.activate
    def test_upload_loser_returns_400_without_orphan_files(self):
        self.assert_cross_route_conflict(
            loser_route="image-create-imageset",
            winner_route="image-create-imageset-from-url",
            loser_status=400,
        )

    def assert_cross_route_conflict(self, loser_route, winner_route, loser_status):
        responses.get(self.remote_url, body=get_example_image_data())
        ready = Event()
        winner_committed = Event()
        insert = ImageSet.objects.create
        attempted_files = []

        def synchronized_insert(**kwargs):
            if kwargs["description"] == "loser":
                attempted_files.extend(
                    kwargs[f"image_{size}"].image.name
                    for size in ("small", "medium", "large")
                )
                ready.set()
                if not winner_committed.wait(timeout=10):
                    raise TimeoutError("Winner did not commit")
            return insert(**kwargs)

        with patch.object(ImageSet.objects, "create", side_effect=synchronized_insert):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.post_image, loser_route, "loser")
                try:
                    self.assertTrue(ready.wait(timeout=10))
                    self.assertEqual(ImageSet.objects.count(), 0)
                    winner = self.post_image(winner_route, "winner")
                    self.assertEqual(winner.status_code, 200)
                finally:
                    winner_committed.set()
                loser = future.result(timeout=20)
        self.assertEqual(loser.status_code, loser_status)
        if loser_status == 200:
            self.assertEqual(loser.data, winner.data)
        else:
            self.assertIn("identifier", loser.data)
            self.assertIn(
                "Er bestaat al een image set met eenzelfde identifier.",
                str(loser.data),
            )
        self.assertEqual(len(self.connection_ids), 2)
        self.assertEqual(len(attempted_files), 3)
        for name in attempted_files:
            self.assertFalse(default_storage.exists(name))
        self.assert_only_winner_survives(winner)

    def test_variant_database_failure_cleans_saved_file(self):
        with patch.object(ImageVariant, "save", side_effect=IntegrityError("variant")):
            with self.assertRaises(IntegrityError):
                image_set.create_set(get_example_image_file(), {})
        self.assertEqual(ImageSet.objects.count(), 0)
        self.assertEqual(ImageVariant.objects.count(), 0)
        self.assertEqual(default_storage.listdir("image")[1], [])

    def test_cleanup_error_is_logged_without_masking_database_error(self):
        failure = IntegrityError("insert failure")
        with (
            patch.object(ImageSet.objects, "create", side_effect=failure),
            patch.object(default_storage, "delete", side_effect=OSError("storage")),
            self.assertLogs(image_set.logger, level="ERROR") as logs,
        ):
            with self.assertRaises(IntegrityError) as caught:
                image_set.create_set(get_example_image_file(), {})
        self.assertIs(caught.exception, failure)
        self.assertEqual(len(logs.output), 3)
        self.assertEqual(ImageSet.objects.count(), 0)
        self.assertEqual(ImageVariant.objects.count(), 0)
