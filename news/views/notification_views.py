import logging

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_device_id
from core.views.mixins import DeviceIdMixin
from news.models import LiveblogNotification, NewsArticle
from news.serializers.notification_serializers import NotificationResponseSerializer

logger = logging.getLogger(__name__)


class NotificationView(DeviceIdMixin, generics.GenericAPIView):
    serializer_class = NotificationResponseSerializer
    http_method_names = ["get", "post", "delete"]

    @extend_schema_for_device_id(
        success_response=NotificationResponseSerializer,
        additional_responses={204: None},
    )
    def get(self, request, *args, **kwargs):
        article_id = kwargs.get("article_id")
        notification = LiveblogNotification.objects.filter(
            device_id=self.device_id,
            article_id=article_id,
        ).first()
        if not notification:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.serializer_class(notification)
        return Response(serializer.data)

    @extend_schema_for_device_id(
        request=None,
        success_response=NotificationResponseSerializer,
        additional_responses={201: NotificationResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        article_id = kwargs.get("article_id")
        liveblog = NewsArticle.visible_objects.filter(
            id=article_id, is_liveblog=True
        ).first()
        if not liveblog:
            raise ValidationError("Article id does not belong to a liveblog")

        notification, created = LiveblogNotification.objects.get_or_create(
            device_id=self.device_id,
            article=liveblog,
        )
        serializer = self.serializer_class(notification)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=response_status)

    @extend_schema_for_device_id(
        success_response=None,
    )
    def delete(self, request, *args, **kwargs):
        article_id = kwargs.get("article_id")
        LiveblogNotification.objects.filter(
            device_id=self.device_id,
            article_id=article_id,
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeviceDataDeleteView(DeviceIdMixin, generics.GenericAPIView):
    http_method_names = ["delete"]

    @extend_schema_for_device_id(
        success_response=None,
        additional_responses={204: None},
        description="Deletes all records for followed liveblogs for the device id provided in the request header.",
    )
    def delete(self, request, *args, **kwargs):
        LiveblogNotification.objects.filter(device_id=self.device_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
