from django.test import TestCase
from model_bakery import baker

from core.utils.device_utils import create_missing_device_ids
from notification.models.notification_models import Device


class TestDeviceUtils(TestCase):
    databases = ["default", "notification"]

    def test_create_success(self):
        create_missing_device_ids(["device_1", "device_2"])
        self.assertEqual(
            Device.objects.filter(external_id__in=["device_1", "device_2"]).count(), 2
        )

    def test_create_repeat(self):
        for _i in range(10):
            create_missing_device_ids(["device_1", "device_2"])
        self.assertEqual(
            Device.objects.filter(external_id__in=["device_1", "device_2"]).count(), 2
        )

    def test_device_already_exist(self):
        baker.make(Device, external_id="foobar")
        create_missing_device_ids(["foobar"])
        self.assertEqual(Device.objects.count(), 1)
