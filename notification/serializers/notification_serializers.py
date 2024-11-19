from django.conf import settings
from rest_framework import serializers

from notification.models import Notification


class NotificationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "module_slug",
            "context",
            "created_at",
            "pushed_at",
            "is_read",
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    client_ids = serializers.ListField(child=serializers.CharField(), write_only=True)

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


class NotificationCreateResponseSerializer(serializers.Serializer):
    total_client_count = serializers.IntegerField()
    total_create_count = serializers.IntegerField()
    total_token_count = serializers.IntegerField()
    failed_token_count = serializers.IntegerField()
    missing_client_ids = serializers.ListField(
        child=serializers.CharField(), allow_empty=True
    )


class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["is_read"]

    def to_representation(self, instance):
        return NotificationResultSerializer(context=self.context).to_representation(
            instance
        )
