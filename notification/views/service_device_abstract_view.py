from rest_framework import generics, status
from rest_framework.response import Response

from core.views.mixins import DeviceIdMixin
from notification.models import Device
from core.utils.openapi_utils import extend_schema_for_device_id
from notification.serializers.device_serializers import ServiceDeviceResponseSerializer

@extend_schema_for_device_id(success_response=ServiceDeviceResponseSerializer)
class ServiceDeviceView(DeviceIdMixin, generics.GenericAPIView):
    """Create/update, retrieve and delete the waste-notification schedule for a device."""

    http_method_names = ["get", "post", "delete"]

    def get(self, request, *args, **kwargs):
        if self._get_instance() is None:
            return Response(
                data={"status": "error", "message": "not found"},
                status=status.HTTP_200_OK,
            )
        return Response({"status": "success"}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        instance = self._get_instance()
        if instance is None:
            serializer = self.get_serializer(
                data=request.data, context={"device_id": self.device_id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            self.get_or_create_device(self.device_id)
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)

        # If instance already exists, update it with the new data, and update updated_at to now
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.get_or_create_device(self.device_id)
        return Response({"status": "success"}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        instance = self._get_instance()
        if instance is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_instance(self):
        """Helper method, should be implemented by the child class, to get the notification instance for the device_id"""
        raise NotImplementedError("Subclasses must implement _get_instance method")
    
    def get_or_create_device(self, device_id):
        existing_device = Device.objects.filter(external_id=device_id).first()
        if not existing_device:
            return Device.objects.create(external_id=device_id)
        else:
            return existing_device
