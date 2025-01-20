import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.serializers.error_serializers import get_error_response_serializers
from notification.exceptions import PushServiceError
from notification.models import Notification
from notification.serializers.image_serializers import (
    ImageSetRequestSerializer,
    ImageSetSerializer,
)
from notification.serializers.notification_serializers import (
    NotificationCreateResponseSerializer,
    NotificationCreateSerializer,
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


class ImageSetCreateView(generics.CreateAPIView):
    """
    Endpoint to create a new image set. This endpoint is network isolated and only accessible from other backend services.

    The image is uploaded in three different formats to Azure Blob Storage and variants are created in the database.
    """

    authentication_classes = (
        []
    )  # No authentication or API key required. Endpoint is not exposed through ingress.
    serializer_class = ImageSetRequestSerializer

    @extend_schema(
        responses={
            200: ImageSetSerializer,
            **get_error_response_serializers([ValidationError]),
        },
    )
    def post(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        imageset = create_serializer.save()
        output_serializer = ImageSetSerializer(imageset)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
