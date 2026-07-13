import requests
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.mijnamsterdam.mock_data import wpi_specification
from bridge.mijnamsterdam.serializers.device_serializers import DeviceResponseSerializer
from bridge.mijnamsterdam.serializers.logout_serializers import (
    LogoutNotificationRequestSerializer,
    LogoutNotificationResponseSerializer,
)
from bridge.mijnamsterdam.services.notifications import LogoutNotificationService
from core.authentication import MijnAmsterdamOutboundKeyAuthentication
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


@extend_schema_for_api_key(success_response=LogoutNotificationResponseSerializer)
class LogoutNotificationView(generics.GenericAPIView):
    authentication_classes = [MijnAmsterdamOutboundKeyAuthentication]
    serializer_class = LogoutNotificationRequestSerializer
    logout_notification_service = LogoutNotificationService()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if len(serializer.validated_data["device_ids"]) > 0:
            self.logout_notification_service.send(
                device_ids=serializer.validated_data["device_ids"]
            )

        response_serializer = LogoutNotificationResponseSerializer(
            data={"status": "OK"}
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema_for_api_key()
class MijnAmsterdamThemesView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):

        response_data = {
            "themes": [
                {
                    "moduleSlug": "mams-income",
                    "version": "1.0.0",
                    "title": "Inkomen",
                    "description": "Inkomen Mijn Amsterdam",
                    "icon": "announcement",
                    "iconPath": "M16.5049 8.42969C17.4919 8.55235 18.2559 9.3929 18.2559 10.4131C18.2559 10.4744 18.2517 10.5349 18.2461 10.5947C18.2449 10.6078 18.2436 10.6208 18.2422 10.6338C18.2398 10.6548 18.2355 10.6755 18.2324 10.6963C18.2237 10.7575 18.2133 10.8177 18.1992 10.877C18.1965 10.8881 18.1933 10.8991 18.1904 10.9102C17.9892 11.6957 17.3255 12.2935 16.5049 12.3955V18.4131L13.3604 17.085V20.7646L11.791 21.5869L7.83496 18.8438C6.99423 18.2607 6.50876 17.289 6.54688 16.2666L6.62207 14.2393L6.33691 14.1191H3.53516L3.33105 14.1084C2.38974 14.013 1.64169 13.2644 1.5459 12.3232L1.53418 12.1191V8.70801C1.53418 7.67236 2.32238 6.82101 3.33105 6.71875L3.53516 6.70801H6.33496L16.5049 2.41309V8.42969ZM8.54492 16.3408C8.53223 16.6816 8.69448 17.0058 8.97461 17.2002L11.3604 18.8535V16.3926L8.58887 15.1709L8.54492 16.3408ZM7.50488 8.38379V12.4414L14.5049 15.3965V5.42871L7.50488 8.38379ZM3.53516 12.1191H5.22754V8.70801H3.53516V12.1191Z M22.3984 14.5957L21.0361 16.0586L18.5156 13.7119C19.0718 13.3302 19.5262 12.8121 19.8311 12.2051L22.3984 14.5957Z M23 9.41406L22.999 11.4141L20.1289 11.4131C20.2112 11.0934 20.2559 10.7585 20.2559 10.4131C20.2559 10.0678 20.2121 9.7327 20.1299 9.41309L23 9.41406Z M22.3984 6.23145L19.8311 8.62109C19.5263 8.01428 19.0725 7.49597 18.5166 7.11426L21.0361 4.76855L22.3984 6.23145Z",
                    "status": 1,
                    "moduleStatus": 1,
                    "moduleAppReason": None,
                    "moduleFallbackUrl": None,
                    "moduleButtonLabel": "Bekijk op Amsterdam.nl",
                    "releaseStatus": 1,
                    "releaseAppReason": None,
                    "releaseFallbackUrl": None,
                    "releaseButtonLabel": "Bekijk op Amsterdam.nl",
                },
                {
                    "moduleSlug": "mams-invoices",
                    "version": "1.0.0",
                    "title": "Facturen",
                    "description": "Facturen Mijn Amsterdam",
                    "icon": "announcement",
                    "iconPath": "M16.5049 8.42969C17.4919 8.55235 18.2559 9.3929 18.2559 10.4131C18.2559 10.4744 18.2517 10.5349 18.2461 10.5947C18.2449 10.6078 18.2436 10.6208 18.2422 10.6338C18.2398 10.6548 18.2355 10.6755 18.2324 10.6963C18.2237 10.7575 18.2133 10.8177 18.1992 10.877C18.1965 10.8881 18.1933 10.8991 18.1904 10.9102C17.9892 11.6957 17.3255 12.2935 16.5049 12.3955V18.4131L13.3604 17.085V20.7646L11.791 21.5869L7.83496 18.8438C6.99423 18.2607 6.50876 17.289 6.54688 16.2666L6.62207 14.2393L6.33691 14.1191H3.53516L3.33105 14.1084C2.38974 14.013 1.64169 13.2644 1.5459 12.3232L1.53418 12.1191V8.70801C1.53418 7.67236 2.32238 6.82101 3.33105 6.71875L3.53516 6.70801H6.33496L16.5049 2.41309V8.42969ZM8.54492 16.3408C8.53223 16.6816 8.69448 17.0058 8.97461 17.2002L11.3604 18.8535V16.3926L8.58887 15.1709L8.54492 16.3408ZM7.50488 8.38379V12.4414L14.5049 15.3965V5.42871L7.50488 8.38379ZM3.53516 12.1191H5.22754V8.70801H3.53516V12.1191Z M22.3984 14.5957L21.0361 16.0586L18.5156 13.7119C19.0718 13.3302 19.5262 12.8121 19.8311 12.2051L22.3984 14.5957Z M23 9.41406L22.999 11.4141L20.1289 11.4131C20.2112 11.0934 20.2559 10.7585 20.2559 10.4131C20.2559 10.0678 20.2121 9.7327 20.1299 9.41309L23 9.41406Z M22.3984 6.23145L19.8311 8.62109C19.5263 8.01428 19.0725 7.49597 18.5166 7.11426L21.0361 4.76855L22.3984 6.23145Z",
                    "status": 1,
                    "moduleStatus": 1,
                    "moduleAppReason": None,
                    "moduleFallbackUrl": None,
                    "moduleButtonLabel": "Bekijk op Amsterdam.nl",
                    "releaseStatus": 1,
                    "releaseAppReason": None,
                    "releaseFallbackUrl": None,
                    "releaseButtonLabel": "Bekijk op Amsterdam.nl",
                },
            ]
        }

        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema_for_api_key()
class MijnAmsterdamThemesDetailView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        service_name = kwargs.get("service_name")
        if service_name == "mams-income":
            response_data = {"wpi_specificaties": wpi_specification.MOCK_DATA}
        else:
            response_data = {"not-implemented": {}}
        return Response(response_data, status=status.HTTP_200_OK)
