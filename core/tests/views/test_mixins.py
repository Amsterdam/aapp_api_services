from django.conf import settings
from django.test import TestCase
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.exceptions import MissingDeviceIdHeader
from core.views.mixins import DeviceIdMixin


class DeviceIdRequiredView(DeviceIdMixin, APIView):
    authentication_classes = []
    permission_classes = []
    device_id_required = True

    def get(self, request):
        return Response({"device_id": self.device_id})


class DeviceIdNotRequiredView(DeviceIdMixin, APIView):
    authentication_classes = []
    permission_classes = []
    device_id_required = False

    def get(self, request):
        return Response({"device_id": self.device_id})


class TestDeviceIdMixin(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_required = DeviceIdRequiredView.as_view()
        self.view_not_required = DeviceIdNotRequiredView.as_view()

    def assert_device_id_present(self, view):
        device_id = "test-device-123"
        request = self.factory.get("/get-device-id/")
        request.headers = {settings.HEADER_DEVICE_ID: device_id}
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device_id"], device_id)

    def test_device_id_present(self):
        self.assert_device_id_present(self.view_required)
        self.assert_device_id_present(self.view_not_required)

    def test_missing_required_device_id_raises_error(self):
        request = self.factory.get("/get-device-id/")
        response = self.view_required(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_missing_not_required_device_id_is_ok(self):
        request = self.factory.get("/get-device-id/")
        response = self.view_not_required(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device_id"], None)

    def test_empty_not_required_device_id_is_ok(self):
        request = self.factory.get("/get-device-id/")
        request.headers = {settings.HEADER_DEVICE_ID: ""}
        response = self.view_not_required(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device_id"], None)
