from rest_framework import serializers

from core.serializers.mixins import PostalCodeValidationMixin


class BurningGuideNotificationRequestSerializer(
    PostalCodeValidationMixin, serializers.Serializer
):
    postal_code = serializers.CharField()


class BurningGuideNotificationResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField(required=False)
