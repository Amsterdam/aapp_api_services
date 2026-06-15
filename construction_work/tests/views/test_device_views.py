import pathlib

from django.conf import settings
from django.urls import reverse
from model_bakery import baker

from construction_work.models.manage_models import (
    Device,
)
from construction_work.models.project_models import Project
from core.tests.test_authentication import BasicAPITestCase

ROOT_DIR = pathlib.Path(__file__).resolve().parents[3]


class TestDeleteDeviceDataView(BasicAPITestCase):
    def setUp(self):
        super().setUp()

        self.project_1 = baker.make(Project)
        self.project_2 = baker.make(Project)

        self.device_1 = baker.make(
            Device,
            device_id="device-1",
            followed_projects=[self.project_1, self.project_2],
        )
        self.device_2 = baker.make(
            Device, device_id="device-2", followed_projects=[self.project_1]
        )

        self.api_url = reverse("construction-work:delete-device-data")

    def test_missing_device_id(self):
        response = self.client.delete(self.api_url, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)

    def test_existing_device_is_deleted(self):

        self.api_headers[settings.HEADER_DEVICE_ID] = self.device_1.device_id
        response = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "deleted")
        self.assertFalse(
            Device.objects.filter(device_id=self.device_1.device_id).exists()
        )
        self.assertTrue(
            Device.objects.filter(device_id=self.device_2.device_id).exists()
        )
        self.assertEqual(Device.objects.count(), 1)

    def test_unknown_device_returns_2xx(self):
        self.api_headers[settings.HEADER_DEVICE_ID] = "unknown-device"

        response = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "already_absent")

    def test_second_call_is_idempotent(self):

        self.api_headers[settings.HEADER_DEVICE_ID] = self.device_1.device_id

        first_response = self.client.delete(self.api_url, headers=self.api_headers)
        second_response = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.data["status"], "deleted")
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.data["status"], "already_absent")
        self.assertFalse(
            Device.objects.filter(device_id=self.device_1.device_id).exists()
        )
