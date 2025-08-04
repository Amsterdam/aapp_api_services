from rest_framework import serializers
from rest_framework.serializers import Serializer


class NotificationSerializer(Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    datePublished = serializers.DateTimeField()
    isTip = serializers.BooleanField(required=False)


class UserSerializer(Serializer):
    # A unique user is defined per BSN
    service_ids = serializers.ListField(child=serializers.CharField())
    consumer_ids = serializers.ListField(child=serializers.CharField())  # Device IDs
    date_updated = serializers.DateTimeField()
    notifications = NotificationSerializer(many=True, required=False)


class MijnAmsNotificationResponseSerializer(Serializer):
    content = UserSerializer(many=True)
    status = serializers.ChoiceField(choices=["OK", "ERROR"])
