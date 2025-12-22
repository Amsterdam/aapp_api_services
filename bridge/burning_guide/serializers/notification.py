from rest_framework import serializers

from bridge.burning_guide.serializers.mixins import PostalCodeValidationMixin
from bridge.models import BurningGuideNotification


class NotificationSerializer(serializers.ModelSerializer, PostalCodeValidationMixin):
    send_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = BurningGuideNotification
        fields = ["postal_code", "send_at"]
