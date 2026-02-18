from datetime import timezone

from rest_framework import serializers
from rest_framework.serializers import Serializer


class NotificationSerializer(Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    themaId = serializers.CharField()
    datePublished = serializers.DateTimeField()

    def validate_datePublished(self, value):
        # Ensure mijnamsterdam datetimes are interpreted as UTC
        return value.replace(tzinfo=timezone.utc)


class ServiceSerializer(Serializer):
    status = serializers.ChoiceField(choices=["OK", "ERROR"])
    content = NotificationSerializer(many=True, allow_null=True)
    serviceId = serializers.CharField()
    dateUpdated = serializers.DateTimeField()

    def validate_dateUpdated(self, value):
        # Ensure mijnamsterdam datetimes are interpreted as UTC
        return value.replace(tzinfo=timezone.utc)

    def validate_content(self, value):
        if value is None:
            return []
        return value


class UserSerializer(Serializer):
    # A unique user is defined per BSN
    services = ServiceSerializer(many=True)
    consumerIds = serializers.ListField(child=serializers.CharField())  # Device IDs
    dateUpdated = serializers.DateTimeField()

    def validate_dateUpdated(self, value):
        # Ensure mijnamsterdam datetimes are interpreted as UTC
        return value.replace(tzinfo=timezone.utc)


class MijnAmsNotificationResponseSerializer(Serializer):
    content = UserSerializer(many=True)
    status = serializers.ChoiceField(choices=["OK", "ERROR"])
