import requests
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.mijnamsterdam.serializers.device_serializers import DeviceResponseSerializer
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

    def get(self, request):
        try:
            serializer = self._get_status(method="get")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            serializer = self._get_status(method="delete")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # reraise error after retries are exhausted
    )
    def _get_status(self, method):
        url = (
            settings.MIJN_AMS_API_DOMAIN
            + settings.MIJN_AMS_API_PATHS["DEVICES"]
            + self.device_id
        )
        response = requests.request(method, url, timeout=10)
        response.raise_for_status()
        json = response.json()
        try:
            status = json["status"]
        except KeyError:
            status = "ERROR"

        serializer = DeviceResponseSerializer(data={"status": status})
        serializer.is_valid(raise_exception=True)
        return serializer
