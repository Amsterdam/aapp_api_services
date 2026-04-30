import logging

from drf_spectacular.utils import inline_serializer
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.response import Response

from core.enums import NotificationType
from core.utils.openapi_utils import (
    extend_schema_for_device_id,
)
from core.views.mixins import DeviceIdMixin
from notification.models import Notification
from notification.serializers.notification_serializers import (
    ModuleNotificationTypeSerializer,
    NotificationResultSerializer,
    NotificationUpdateSerializer,
)

logger = logging.getLogger(__name__)


class NotificationListView(DeviceIdMixin, generics.ListAPIView):
    """List all notifications for a device_id."""

    serializer_class = NotificationResultSerializer

    def get_queryset(self):
        return (
            Notification.objects.select_related("device")
            .filter(device__external_id=self.device_id)
            .filter(is_visible=True)
            .order_by("-created_at")
        )

    @extend_schema_for_device_id(
        success_response=NotificationResultSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NotificationMarkAllReadView(DeviceIdMixin, generics.UpdateAPIView):
    """Update all notification for a device_id to status "is_read" = true."""

    http_method_names = ["post"]

    @extend_schema_for_device_id(
        success_response=inline_serializer(
            name="MarkAllAsReadResponse", fields={"detail": CharField()}
        )
    )
    def post(self, request, *args, **kwargs):
        # Perform the bulk update
        updated_count = (
            Notification.objects.select_related("device")
            .filter(device_external_id=self.device_id, is_read=False, is_visible=True)
            .update(is_read=True)
        )
        return Response({"detail": f"{updated_count} notifications marked as read."})


class NotificationDetailView(DeviceIdMixin, generics.RetrieveUpdateAPIView):
    serializer_class = NotificationResultSerializer
    lookup_url_kwarg = "notification_id"
    lookup_field = "id"
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        return (
            Notification.objects.select_related("device")
            .filter(device__external_id=self.device_id)
            .filter(is_visible=True)
        )
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)
        filter_kwargs = {self.lookup_field: lookup_value}
        try:
            return queryset.get(**filter_kwargs)
        except Notification.DoesNotExist:
            return None  # or handle as you wish
    
    @extend_schema_for_device_id(
        success_response=NotificationResultSerializer,
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a single notification."""
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "No Notification matches the given query."},
                status=status.HTTP_204_NO_CONTENT,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema_for_device_id(
        request=NotificationUpdateSerializer,
        success_response=NotificationResultSerializer,
        exceptions=[ValidationError],
    )
    def patch(self, request, *args, **kwargs):
        """Update a single notification to status "is_read" = true."""
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "No Notification matches the given query."},
                status=status.HTTP_204_NO_CONTENT,
            )
        serializer = NotificationUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NotificationModulesView(generics.ListAPIView):
    """
    List all modules that can be used to send notifications.
    """

    serializer_class = ModuleNotificationTypeSerializer

    def get_queryset(self):
        return NotificationType.get_modules_with_types_and_descriptions()
