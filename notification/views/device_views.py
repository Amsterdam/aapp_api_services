from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from core.exceptions import InputDataException, MissingDeviceIdHeader
from core.views.extend_schema import extend_schema_for_device_id
from notification.models import Device
from notification.serializers.device_serializers import (
    DeviceRegisterRequestSerializer,
    DeviceRegisterResponseSerializer,
)


class DeviceRegisterView(generics.GenericAPIView):
    """
    API view to register or unregister a device.
    """

    @extend_schema_for_device_id(
        request=DeviceRegisterRequestSerializer,
        success_response=DeviceRegisterResponseSerializer,
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

        serializer = DeviceRegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device, created = Device.objects.get_or_create(
            external_id=device_id, defaults=serializer.validated_data
        )
        return Response(
            DeviceRegisterResponseSerializer(device).data, status=status.HTTP_200_OK
        )

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
