from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from core.exceptions import InputDataException, MissingDeviceIdHeader
from core.views.extend_schema import extend_schema_for_device_id
from notification.models import Device
from notification.serializers.device_serializers import (
    DeviceRegisterPostSwaggerSerializer,
    DeviceRegisterSerializer,
)


class DeviceRegisterView(generics.GenericAPIView):
    """
    API view to register or unregister a device.
    """

    @extend_schema_for_device_id(
        request=DeviceRegisterPostSwaggerSerializer,
        success_response=DeviceRegisterSerializer,
        exceptions=[InputDataException],
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
        request_data["external_id"] = device_id

        # Retrieve the device if it exists
        device = Device.objects.filter(external_id=device_id).first()

        # Initialize the serializer with instance for update or None for create
        serializer = DeviceRegisterSerializer(instance=device, data=request_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema_for_device_id(
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
            device = Device.objects.get(external_id=device_id)
        except Device.DoesNotExist:
            return Response(
                data="Device is not found, but that's okay",
                status=status.HTTP_200_OK,
            )

        # Remove the Firebase token
        device.firebase_token = None
        device.save()

        return Response("Registration removed", status=status.HTTP_200_OK)
