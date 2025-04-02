from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import MissingDeviceIdHeader
from core.utils.openapi_utils import extend_schema_for_device_id
from waste.models import NotificationSchedule
from waste.serializers.waste_guide_serializers import (
    WasteNotificationResponseSerializer,
    WasteRequestSerializer,
)


class WasteGuideNotificationView(APIView):
    serializer_class = WasteRequestSerializer

    @extend_schema_for_device_id(
        success_response=WasteNotificationResponseSerializer,
        exceptions=[NotFound],
    )
    def get(self, request):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader
        scheduled_notification = get_object_or_404(
            NotificationSchedule, device_id=device_id
        )

        return Response(
            WasteNotificationResponseSerializer(scheduled_notification).data
        )

    @extend_schema_for_device_id(
        request=WasteRequestSerializer,
        success_response=WasteNotificationResponseSerializer,
    )
    def post(self, request):
        bag_nummeraanduiding_id, device_id = self.assert_request(request)
        scheduled_notification = NotificationSchedule.objects.filter(
            device_id=device_id
        ).first()
        if scheduled_notification:
            scheduled_notification.bag_nummeraanduiding_id = bag_nummeraanduiding_id
        else:
            scheduled_notification = NotificationSchedule(
                device_id=device_id, bag_nummeraanduiding_id=bag_nummeraanduiding_id
            )
        scheduled_notification.save()
        return Response(
            WasteNotificationResponseSerializer(scheduled_notification).data
        )

    @extend_schema_for_device_id(
        request=WasteRequestSerializer,
        success_response=WasteNotificationResponseSerializer,
        exceptions=[NotFound],
    )
    def patch(self, request):
        bag_nummeraanduiding_id, device_id = self.assert_request(request)
        scheduled_notification = get_object_or_404(
            NotificationSchedule, device_id=device_id
        )
        scheduled_notification.bag_nummeraanduiding_id = bag_nummeraanduiding_id
        scheduled_notification.save()

        return Response(
            WasteNotificationResponseSerializer(scheduled_notification).data
        )

    @extend_schema_for_device_id(exceptions=[NotFound])
    def delete(self, request):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader
        scheduled_notification = get_object_or_404(
            NotificationSchedule, device_id=device_id
        )
        scheduled_notification.delete()

        return Response(
            data={"message": "Notification deleted successfully"},
            status=status.HTTP_200_OK,
        )

    def assert_request(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        return serializer.validated_data["bag_nummeraanduiding_id"], device_id
