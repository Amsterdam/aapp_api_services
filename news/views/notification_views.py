import logging

from rest_framework import generics, status
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from news.models import LiveblogNotification
from news.serializers.notification_serializers import (
    NotificationRequestSerializer,
    NotificationResponseSerializer,
)

logger = logging.getLogger(__name__)


class NotificationView(DeviceIdMixin, generics.GenericAPIView):
    serializer_class = NotificationResponseSerializer
    http_method_names = ["get", "post", "delete"]

    @extend_schema_for_device_id(
        success_response=NotificationResponseSerializer,
        additional_responses={204: None},
    )
    def get(self, request, *args, **kwargs):
        article = LiveblogNotification.objects.filter(device_id=self.device_id).first()
        if not article:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.serializer_class(article)
        return Response(serializer.data)

    @extend_schema_for_device_id(
        success_response=NotificationResponseSerializer,
        request=NotificationRequestSerializer,
    )
    def post(self, request, *args, **kwargs):
        request_serializer = NotificationRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        article = request_serializer.validated_data["article"]

        notification, _ = LiveblogNotification.objects.update_or_create(
            device_id=self.device_id,
            defaults={
                "article": article,
            },
        )
        serializer = self.serializer_class(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema_for_device_id(
        success_response=None,
    )
    def delete(self, request, *args, **kwargs):
        LiveblogNotification.objects.filter(device_id=self.device_id).delete()
        return Response(status=status.HTTP_200_OK)
