from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from notification.models import Notification
from notification.serializers import (
    NotificationCreateSerializer,
    NotificationResultSerializer,
)
from notification.services.push import PushService


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

    @extend_schema(responses={200: NotificationResultSerializer})
    def post(self, request, *args, **kwargs):
        # NOTE: Construction work should add this data as context_json:
        # {
        #     "linkSourceid": str(warning.pk),
        #     "type": "ProjectWarningCreatedByProjectManager",
        # }
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use serializer data to initialize, but not save, notification
        client_ids = serializer.validated_data.pop("client_ids")
        notification = Notification(**serializer.validated_data)

        push_service = PushService(notification, client_ids)
        push_service.push()

        # Reinitalize the serializer with notification instance
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
