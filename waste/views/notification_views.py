from django.db import IntegrityError
from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, ApiView
from rest_framework.response import Response
import requests
from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from waste.models import WasteNotification
# from waste.serializers.waste_guide_serializers import (
#     WasteNotificationSerializer,
# )


# @extend_schema_for_device_id(success_response=WasteNotificationSerializer)
class WasteNotificationCreateView(DeviceIdMixin, ApiView):
    # serializer_class = WasteNotificationSerializer

    def create(self, request, *args, **kwargs):

        try:
            response = requests.post(
                url=settings.NOTIFICATION_ENDPOINTS["waste_create"],
                headers={"deviceId": self.device_id},
                data=request.data
            )
            response.raise_for_status()
        except:
            return Response(
                {"detail": "Failed to create notification schedule."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "success"}, status=status.HTTP_201_CREATED
        )

        serializer = self.get_serializer(
            data=request.data, context={"device_id": self.device_id}
        )
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {"detail": "Notification schedule for this device already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"status": "success"}, status=status.HTTP_201_CREATED, headers=headers
        )


# @extend_schema_for_device_id(success_response=WasteNotificationSerializer)
class WasteNotificationDetailView(DeviceIdMixin, ApiView):
    # queryset = WasteNotification.objects.all()
    # serializer_class = WasteNotificationSerializer
    # lookup_field = "device_id"
    http_method_names = ["get", "patch", "delete"]

    def get(self):
        try:
            response = requests.get(
                url=settings.NOTIFICATION_ENDPOINTS["waste_create"],
                headers={"deviceId": self.device_id},
            )
            response.raise_for_status()
        except:
            return Response(
                {"detail": "Failed to get waste notification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "success"}, status=status.HTTP_201_CREATED
        )

    def update(self, request):
        try:
            response = requests.patch(
                url=settings.NOTIFICATION_ENDPOINTS["waste_create"],
                headers={"deviceId": self.device_id},
                data=request.data
            )
            response.raise_for_status()
        except:
            return Response(
                {"detail": "Failed to update notification schedule."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "success"}, status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        try:
            response = requests.delete(
                url=settings.NOTIFICATION_ENDPOINTS["waste_create"],
                headers={"deviceId": self.device_id},
                data=request.data
            )
            response.raise_for_status()
        except:
            return Response(
                {"detail": "Failed to delete notification schedule."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "success"}, status=status.HTTP_201_CREATED
        )


    # def get_object(self):
    #     return self.get_queryset().get(device_id=self.device_id)

    # def retrieve(self, request, *args, **kwargs):
    #     try:
    #         self.get_object()
    #     except WasteNotification.DoesNotExist:
    #         return Response(data={"status": "error", "message": "not found"})
    #     return Response({"status": "success"})

    # def update(self, request, *args, **kwargs):
    #     try:
    #         instance = self.get_object()
    #     except WasteNotification.DoesNotExist:
    #         return Response(status=status.HTTP_404_NOT_FOUND)

    #     serializer = self.get_serializer(instance, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     return Response({"status": "success"})

    # def destroy(self, request, *args, **kwargs):
    #     try:
    #         instance = self.get_object()
    #     except WasteNotification.DoesNotExist:
    #         return Response(status=status.HTTP_204_NO_CONTENT)

    #     instance.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)
