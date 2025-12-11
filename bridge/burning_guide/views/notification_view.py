from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView

from bridge.burning_guide.serializers.notification import (
    NotificationCreateSerializer,
    NotificationResponseSerializer,
)
from bridge.models import BurningGuideNotification
from core.utils.openapi_utils import extend_schema_for_api_key


@extend_schema_for_api_key(success_response=NotificationResponseSerializer)
class BurningGuideNotificationCreateView(CreateAPIView):
    serializer_class = NotificationCreateSerializer


@extend_schema_for_api_key(success_response=NotificationResponseSerializer)
class BurningGuideNotificationView(RetrieveUpdateDestroyAPIView):
    queryset = BurningGuideNotification.objects.all()
    serializer_class = NotificationResponseSerializer
    lookup_field = "device_id"
    http_method_names = ["get", "patch", "delete"]
