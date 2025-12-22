from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from waste.models import NotificationSchedule
from waste.serializers.waste_guide_serializers import (
    WasteNotificationSerializer,
)


@extend_schema_for_device_id(success_response=WasteNotificationSerializer)
class WasteNotificationCreateView(DeviceIdMixin, CreateAPIView):
    serializer_class = WasteNotificationSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["device_id"] = self.device_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


@extend_schema_for_device_id(success_response=WasteNotificationSerializer)
class WasteNotificationDetailView(DeviceIdMixin, RetrieveUpdateDestroyAPIView):
    queryset = NotificationSchedule.objects.all()
    serializer_class = WasteNotificationSerializer
    lookup_field = "device_id"
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        return self.get_queryset().get(device_id=self.device_id)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except NotificationSchedule.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except NotificationSchedule.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except NotificationSchedule.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
