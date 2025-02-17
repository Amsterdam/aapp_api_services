import logging

from django.conf import settings
from drf_spectacular.utils import inline_serializer
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.response import Response

from core.exceptions import MissingDeviceIdHeader
from core.utils.openapi_utils import extend_schema_for_device_id
from notification.models import Notification
from notification.serializers.notification_serializers import (
    NotificationResultSerializer,
    NotificationUpdateSerializer,
)

logger = logging.getLogger(__name__)


class NotificationListView(generics.ListAPIView):
    """List all notifications for a device_id."""

    serializer_class = NotificationResultSerializer

    def get_queryset(self):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader
        return Notification.objects.filter(device__external_id=device_id).order_by(
            "-created_at"
        )

    @extend_schema_for_device_id(
        success_response=NotificationResultSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NotificationMarkAllReadView(generics.UpdateAPIView):
    """Update all notification for a device_id to status "is_read" = true."""

    http_method_names = ["post"]

    @extend_schema_for_device_id(
        success_response=inline_serializer(
            name="MarkAllAsReadResponse", fields={"detail": CharField()}
        )
    )
    def post(self, request, *args, **kwargs):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        # Perform the bulk update
        updated_count = Notification.objects.filter(
            device__external_id=device_id, is_read=False
        ).update(is_read=True)
        return Response({"detail": f"{updated_count} notifications marked as read."})


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationResultSerializer
    lookup_url_kwarg = "notification_id"
    lookup_field = "id"
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader
        return Notification.objects.filter(device__external_id=device_id)

    @extend_schema_for_device_id(
        success_response=NotificationResultSerializer,
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a single notification."""
        return super().get(request, *args, **kwargs)

    @extend_schema_for_device_id(
        request=NotificationUpdateSerializer,
        success_response=NotificationResultSerializer,
        exceptions=[ValidationError],
    )
    def patch(self, request, *args, **kwargs):
        """Update a single notification to status "is_read" = true."""
        instance = self.get_object()
        serializer = NotificationUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
