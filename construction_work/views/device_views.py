from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, views
from rest_framework.response import Response

from construction_work.exceptions import MissingDeviceIdHeader
from construction_work.models import Device
from construction_work.serializers import (
    DeviceRegisterPostSwaggerSerializer,
    DeviceRegistrationSerializer,
)


class DeviceRegisterView(views.APIView):
    """
    API view to register or unregister a device.
    """

    @extend_schema(
        parameters=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            )
        ],
        request=DeviceRegisterPostSwaggerSerializer,
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
        parameters=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            )
        ]
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
