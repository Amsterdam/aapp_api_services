from rest_framework import serializers

from bridge.burning_guide.serializers.mixins import PostalCodeValidationMixin
from bridge.models import BurningGuideNotification


class NotificationSerializer(serializers.ModelSerializer, PostalCodeValidationMixin):
    send_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = BurningGuideNotification
        fields = ["postal_code", "send_at"]

    def create(self, validated_data):
        device_id = self.context.get("device_id")
        if not device_id:
            raise serializers.ValidationError("Device ID header missing")

        return BurningGuideNotification.objects.create(
            device_id=device_id,
            **validated_data,
        )
