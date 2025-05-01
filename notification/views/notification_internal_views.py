import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.serializers.error_serializers import get_error_response_serializers
from core.services.notificiation import NotificationServiceError
from notification.crud import NotificationCRUD
from notification.exceptions import PushServiceError
from notification.models import Device, Notification, ScheduledNotification
from notification.serializers.notification_serializers import (
    NotificationCreateResponseSerializer,
    NotificationCreateSerializer,
    ScheduledNotificationDetailSerializer,
    ScheduledNotificationSerializer,
)

logger = logging.getLogger(__name__)


class NotificationInitView(generics.CreateAPIView):
    """
    Endpoint to initialize a new notification. This endpoint is network isolated and only accessible from other backend services.

    The supplied notification data does not represent a final notification object one-to-one.
    The data will be passed to the push service which takes over from that point.

    Response: notification data as posted with auto set fields
    """

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
        notification_crud = NotificationCRUD(notification)

        logger.info(f"Processing new notification: {notification}")
        devices_qs = self.get_device_queryset(device_ids)
        try:
            response_data = notification_crud.create(devices_qs)
        except Exception:
            logger.error("Failed to push notification", exc_info=True)
            raise NotificationServiceError("Failed to push notification")

        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def get_device_queryset(device_ids):
        known_devices_qs = Device.objects.filter(external_id__in=device_ids).all()
        known_device_ids = [device.external_id for device in known_devices_qs]
        unknown_device_ids = set(device_ids) - set(known_device_ids)
        if not unknown_device_ids:
            return known_devices_qs

        Device.objects.bulk_create(
            Device(external_id=device_id) for device_id in unknown_device_ids
        )
        new_devices_qs = Device.objects.filter(external_id__in=unknown_device_ids)
        logger.warning(f"Created {len(new_devices_qs)} unknown devices.")
        devices_qs = known_devices_qs | new_devices_qs
        return devices_qs


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

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if request.method in ["PATCH", "DELETE"]:
            instance = self.get_object()
            if instance.pushed_at:
                raise ValidationError("Cannot modify a pushed notification.")

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
