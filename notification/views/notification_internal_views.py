import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.serializers.error_serializers import get_error_response_serializers
from notification.exceptions import PushServiceError
from notification.models import Device, Notification, ScheduledNotification
from notification.serializers.notification_serializers import (
    NotificationCreateResponseSerializer,
    NotificationCreateSerializer,
    ScheduledNotificationDetailSerializer,
    ScheduledNotificationSerializer,
)
from notification.services.push import PushService

logger = logging.getLogger(__name__)


class NotificationInitView(generics.CreateAPIView):
    """
    Endpoint to initialize a new notification. This endpoint is network isolated and only accessible from other backend services.

    The supplied notification data does not represent a final notification object one-to-one.
    The data will be passed to the push service which takes over from that point.

    Response: notification data as posted with auto set fields
    """

    authentication_classes = (
        []
    )  # No authentication or API key required. Endpoint is not exposed through ingress.
    serializer_class = NotificationCreateSerializer

    @extend_schema(
        responses={
            200: NotificationCreateResponseSerializer,
            **get_error_response_serializers([PushServiceError, ValidationError]),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_ids = serializer.validated_data.pop("device_ids")
        notification = Notification(**serializer.validated_data)

        try:
            push_service = PushService(notification, device_ids)
            response_data = push_service.push()
        except Exception:
            logger.error("Failed to push notification", exc_info=True)
            raise PushServiceError("Failed to push notification")

        return Response(response_data, status=status.HTTP_200_OK)


class ScheduledNotificationView(ModelViewSet):
    serializer_class = ScheduledNotificationSerializer
    queryset = ScheduledNotification.objects.all()

    def create(self, request, *args, **kwargs):
        create_missing_device_ids(request)
        return super().create(request, *args, **kwargs)


class ScheduledNotificationDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ScheduledNotification.objects.all()
    serializer_class = ScheduledNotificationDetailSerializer
    lookup_field = "identifier"
    http_method_names = ["get", "patch", "delete"]

    def update(self, request, *args, **kwargs):
        create_missing_device_ids(request)
        return super().update(request, *args, **kwargs)


def create_missing_device_ids(request):
    device_ids = request.data.get("device_ids", [])
    existing_devices = Device.objects.filter(external_id__in=device_ids).values_list(
        "external_id", flat=True
    )
    missing_device_ids = set(device_ids) - set(existing_devices)
    if missing_device_ids:
        Device.objects.bulk_create(
            Device(external_id=device_id) for device_id in missing_device_ids
        )
    logger.warning(f"Created {len(missing_device_ids)} missing devices.")
