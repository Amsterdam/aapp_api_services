import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from core.serializers.error_serializers import get_error_response_serializers
from notification.exceptions import PushServiceError
from notification.models import Notification
from notification.serializers import (
    NotificationCreateSerializer,
    NotificationResultSerializer,
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

    authentication_classes = []
    serializer_class = NotificationCreateSerializer

    @extend_schema(
        responses={
            200: NotificationResultSerializer,
            **get_error_response_serializers([PushServiceError]),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_ids = serializer.validated_data.pop("client_ids")
        notification = Notification(**serializer.validated_data)

        try:
            push_service = PushService(notification, client_ids)
            push_service.push()
        except Exception:
            logger.error("Failed to push notification", exc_info=True)
            raise PushServiceError("Failed to push notification")

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
