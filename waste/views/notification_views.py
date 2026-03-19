import logging

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from waste.serializers.waste_guide_serializers import WasteRequestSerializer

logger = logging.getLogger(__name__)


@extend_schema_for_device_id()
class WasteNotificationCreateView(DeviceIdMixin, CreateAPIView):
    serializer_class = WasteRequestSerializer

    def create(self, request, *args, **kwargs):
        try:
            response = requests.post(
                url=settings.NOTIFICATION_ENDPOINTS["WASTE_CREATE"],
                data=request.data,
                headers={
                    "DeviceId": self.device_id,
                    settings.API_KEY_HEADER: request.headers.get(
                        settings.API_KEY_HEADER
                    ),
                },
            )
            if response.status_code == status.HTTP_409_CONFLICT:
                return Response(
                    {"detail": "Notification schedule for this device already exists."},
                    status=status.HTTP_409_CONFLICT,
                )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error sending waste notification: {e}")
            return Response(
                {"status": "error", "message": "Failed to send notification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)


@extend_schema_for_device_id()
class WasteNotificationDetailView(DeviceIdMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = WasteRequestSerializer
    http_method_names = ["get", "patch", "delete"]

    def retrieve(self, request, *args, **kwargs):
        try:
            response = requests.get(
                url=settings.NOTIFICATION_ENDPOINTS["WASTE_CHANGE"],
                headers={
                    "DeviceId": self.device_id,
                    settings.API_KEY_HEADER: request.headers.get(
                        settings.API_KEY_HEADER
                    ),
                },
            )
            if response.status_code == status.HTTP_409_CONFLICT:
                return Response(
                    {"detail": "Notification schedule for this device already exists."},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(response.json(), status=response.status_code)

        except Exception:
            logger.error("Error retrieving notification")
            return Response(data={"status": "error", "message": "not found"})

    def update(self, request, *args, **kwargs):
        try:
            response = requests.patch(
                url=settings.NOTIFICATION_ENDPOINTS["WASTE_CHANGE"],
                data=request.data,
                headers={
                    "DeviceId": self.device_id,
                    settings.API_KEY_HEADER: request.headers.get(
                        settings.API_KEY_HEADER
                    ),
                },
            )
            if response.status_code == status.HTTP_404_NOT_FOUND:
                return Response(
                    {"detail": "Notification not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error sending waste notification: {e}")
            return Response(
                {"status": "error", "message": "Failed to send notification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({"status": "success"})

    def destroy(self, request, *args, **kwargs):
        try:
            response = requests.delete(
                url=settings.NOTIFICATION_ENDPOINTS["WASTE_CHANGE"],
                headers={
                    "DeviceId": self.device_id,
                    settings.API_KEY_HEADER: request.headers.get(
                        settings.API_KEY_HEADER
                    ),
                },
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error sending waste notification: {e}")
            return Response(
                {"status": "error", "message": "Failed to send notification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
