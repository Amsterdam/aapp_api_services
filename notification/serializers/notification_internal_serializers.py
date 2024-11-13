from django.conf import settings
from rest_framework import serializers

from notification.models import Notification
from notification.serializers.notification_serializers import (
    NotificationResultSerializer,
)


class NotificationCreateSerializer(serializers.ModelSerializer):
    client_ids = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Notification
        fields = ["title", "body", "module_slug", "context", "created_at", "client_ids"]

    def validate_client_ids(self, client_ids):
        max_clients = settings.MAX_CLIENTS_PER_REQUEST
        if len(client_ids) > settings.MAX_CLIENTS_PER_REQUEST:
            raise serializers.ValidationError(
                f"Too many client ids [{len(client_ids)=}, {max_clients=}]"
            )
        return client_ids

    def validate_context(self, context):
        if not isinstance(context, dict):
            raise serializers.ValidationError("Context must be a dictionary")
        return context

    def to_representation(self, instance):
        return NotificationResultSerializer(context=self.context).to_representation(
            instance
        )
