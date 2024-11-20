import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.serializers.error_serializers import get_error_response_serializers
from notification.exceptions import PushServiceError
from notification.models import Notification
from notification.serializers.notification_serializers import (
    NotificationCreateResponseSerializer,
    NotificationCreateSerializer,
)
from notification.services.push import PushService

logger = logging.getLogger(__name__)


class NotificationInitView(generics.CreateAPIView):
    """
    Endpoint to initialize a new notification.
    The supplied notification data does not represent a final notification object one-to-one.
    The data will be passed to the push service which takes over from that point.

    Returns:
        Response: notification data as posted with auto set fields
    """

    authentication_classes = (
        []
    )  # No authentication or API key required. Endpoint is not exposed to the public.
    serializer_class = NotificationCreateSerializer

    @extend_schema(
        responses={
            201: NotificationCreateResponseSerializer,
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

        return Response(response_data, status=status.HTTP_201_CREATED)
