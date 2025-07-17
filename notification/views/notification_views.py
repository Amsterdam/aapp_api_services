import logging

from drf_spectacular.utils import inline_serializer
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from notification.models import Notification, NotificationLast
from notification.serializers.notification_serializers import (
    NotificationLastRequestSerializer,
    NotificationLastResultSerializer,
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
            .filter(device__external_id=self.device_id, is_read=False)
            .update(is_read=True)
        )
        return Response({"detail": f"{updated_count} notifications marked as read."})


class NotificationDetailView(DeviceIdMixin, generics.RetrieveUpdateAPIView):
    serializer_class = NotificationResultSerializer
    lookup_url_kwarg = "notification_id"
    lookup_field = "id"
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        return Notification.objects.select_related("device").filter(
            device__external_id=self.device_id
        )

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


class NotificationLastView(DeviceIdMixin, generics.ListAPIView):
    """
    Retrieve the last push notification for a device_id.
    This is used to determine if the last push notification was read or not.
    """

    serializer_class = NotificationLastResultSerializer
    request_serializer_class = NotificationLastRequestSerializer
    http_method_names = ["get"]

    def get_queryset(self):
        request = self.request_serializer_class(data=self.request.query_params)
        request.is_valid(raise_exception=True)

        return NotificationLast.objects.select_related("device").filter(
            device__external_id=self.device_id,
            module_slug=request.validated_data["module_slug"],
        )

    @extend_schema_for_device_id(
        success_response=NotificationLastResultSerializer(many=True),
        additional_params=[NotificationLastRequestSerializer],
    )
    def get(self, request, *args, **kwargs):
        """Retrieve the last push notification."""
        return super().get(request, *args, **kwargs)
