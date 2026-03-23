from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from bridge.burning_guide.serializers.advice import (
    AdviceRequestSerializer,
)
from core.services.internal_http_client import InternalServiceSession
from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin

internal_client = InternalServiceSession()


@extend_schema_for_device_id()
class BurningGuideNotificationCreateView(DeviceIdMixin, CreateAPIView):
    serializer_class = AdviceRequestSerializer

    def create(self, request, *args, **kwargs):
        response = internal_client.post(
            url=settings.NOTIFICATION_ENDPOINT["BURNING_GUIDE"],
            data=request.data,
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(response.json(), status=response.status_code)


@extend_schema_for_device_id()
class BurningGuideNotificationView(DeviceIdMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = AdviceRequestSerializer
    http_method_names = ["get", "patch", "delete"]

    def retrieve(self, request, *args, **kwargs):
        response = internal_client.get(
            url=settings.NOTIFICATION_ENDPOINT["BURNING_GUIDE"],
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(response.json(), status=response.status_code)

    def update(self, request, *args, **kwargs):
        response = internal_client.post(
            url=settings.NOTIFICATION_ENDPOINT["BURNING_GUIDE"],
            data=request.data,
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(response.json(), status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        internal_client.delete(
            url=settings.NOTIFICATION_ENDPOINT["BURNING_GUIDE"],
            headers={
                settings.HEADER_DEVICE_ID: self.device_id,
                settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
