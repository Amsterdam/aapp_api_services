from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from core.services.internal_http_client import InternalServiceSession
from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from waste.serializers.waste_guide_serializers import (
    WasteNotificationResponseSerializer,
    WasteRequestSerializer,
)

internal_client = InternalServiceSession()


@extend_schema_for_device_id(success_response=WasteNotificationResponseSerializer)
class WasteNotificationCreateView(DeviceIdMixin, CreateAPIView):
    serializer_class = WasteRequestSerializer

    def create(self, request, *args, **kwargs):
        response = internal_client.post(
            url=settings.NOTIFICATION_ENDPOINT["WASTE"],
            data=request.data,
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(response.json(), status=response.status_code)


@extend_schema_for_device_id(success_response=WasteNotificationResponseSerializer)
class WasteNotificationDetailView(DeviceIdMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = WasteRequestSerializer
    http_method_names = ["get", "patch", "delete"]

    def retrieve(self, request, *args, **kwargs):
        response = internal_client.get(
            url=settings.NOTIFICATION_ENDPOINT["WASTE"],
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(response.json(), status=response.status_code)

    def update(self, request, *args, **kwargs):
        response = internal_client.post(
            url=settings.NOTIFICATION_ENDPOINT["WASTE"],
            data=request.data,
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(response.json(), status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        internal_client.delete(
            url=settings.NOTIFICATION_ENDPOINT["WASTE"],
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
