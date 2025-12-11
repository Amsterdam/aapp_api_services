from rest_framework import serializers

from bridge.burning_guide.serializers.mixins import PostalCodeValidationMixin
from bridge.models import BurningGuideNotification


class NotificationCreateSerializer(
    serializers.ModelSerializer, PostalCodeValidationMixin
):
    class Meta:
        model = BurningGuideNotification
        fields = ["device_id", "postal_code"]


class NotificationResponseSerializer(
    serializers.ModelSerializer, PostalCodeValidationMixin
):
    send_at = serializers.DateTimeField(read_only=True)
    device_id = serializers.CharField(read_only=True)

    class Meta:
        model = BurningGuideNotification
        fields = "__all__"
