from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response

from construction_work.exceptions import MissingDeviceIdHeader
from construction_work.models import Device
from construction_work.serializers.device_serializers import (
    DeviceRegisterPostSwaggerSerializer,
    DeviceRegistrationSerializer,
)
from core.exceptions import InputDataException
from core.views.extend_schema import extend_schema_for_api_key as extend_schema


class DeviceRegisterView(generics.GenericAPIView):
    """
    API view to register or unregister a device.
    """

    @extend_schema(
        request=DeviceRegisterPostSwaggerSerializer,
        success_response=DeviceRegistrationSerializer,
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            )
        ],
        exceptions=[MissingDeviceIdHeader, InputDataException],
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new device with firebase token and os if device id is not known yet.
        Update device with firebase token and os if device is already known.
        """
        device_id = request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        # Include 'device_id' in the serializer data
        request_data = request.data.copy()
        request_data["device_id"] = device_id

        # Retrieve the device if it exists
        device = Device.objects.filter(device_id=device_id).first()

        # Initialize the serializer with instance for update or None for create
        serializer = DeviceRegistrationSerializer(instance=device, data=request_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            )
        ],
        exceptions=[MissingDeviceIdHeader],
        success_response={200: None},
    )
    def delete(self, request, *args, **kwargs):
        """
        Unregister a device by removing its Firebase token.
        """
        device_id = request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response(
                data="Device is not found, but that's okay",
                status=status.HTTP_200_OK,
            )

        # Remove the Firebase token
        device.firebase_token = None
        device.save()

        return Response("Registration removed", status=status.HTTP_200_OK)
