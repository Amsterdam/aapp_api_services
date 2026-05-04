import requests
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.mijnamsterdam.serializers.device_serializers import DeviceResponseSerializer
from core.enums import Module
from core.services.notification_last import NotificationLastService
from core.utils.openapi_utils import extend_schema_for_api_key
from core.views.mixins import DeviceIdMixin


@extend_schema_for_api_key(
    success_response=DeviceResponseSerializer,
    additional_params=[
        OpenApiParameter(
            settings.HEADER_DEVICE_ID,
            OpenApiTypes.STR,
            OpenApiParameter.HEADER,
            required=True,
        )
    ],
)
class MijnAmsterdamDeviceView(DeviceIdMixin, generics.GenericAPIView):
    serializer_class = DeviceResponseSerializer
    notification_last_service = NotificationLastService(
        module_slug=Module.MIJN_AMS.value
    )

    def get(self, request):
        try:
            response_json = self._get_device_response(method="get")
            content = response_json["content"]
            if content.get("isRegistered"):
                profile_name = content.get("profileName")
                data = {"status": "OK", "profile_name": profile_name}
            else:
                data = {"status": "ERROR"}
            serializer = DeviceResponseSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            response_json = self._get_device_response(method="delete")
            data = {"status": response_json["status"]}
            serializer = DeviceResponseSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.notification_last_service.delete_last_timestamps(
                device_id=self.device_id
            )

            return Response(serializer.data, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # reraise error after retries are exhausted
    )
    def _get_device_response(self, method):
        url = (
            settings.MIJN_AMS_API_DOMAIN
            + settings.MIJN_AMS_API_PATHS["DEVICES"]
            + self.device_id
        )
        headers = {
            settings.MIJN_AMS_API_KEY_HEADER: settings.MIJN_AMS_API_KEY_INBOUND,
        }
        response = requests.request(method, url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
