from django.conf import settings
from rest_framework import serializers

from notification.models import ImageSet, Notification
from notification.serializers.image_serializers import ImageSetSerializer


class NotificationResultSerializer(serializers.ModelSerializer):
    image = ImageSetSerializer(source="image_set", required=False)

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
            "image",
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    device_ids = serializers.ListField(child=serializers.CharField(), write_only=True)
    image = serializers.PrimaryKeyRelatedField(
        queryset=ImageSet.objects.all(),
        source="image_set",
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Notification
        fields = [
            "title",
            "body",
            "module_slug",
            "context",
            "created_at",
            "device_ids",
            "image",
        ]

    def validate_device_ids(self, device_ids):
        max_devices = settings.MAX_DEVICES_PER_REQUEST
        if len(device_ids) > settings.MAX_DEVICES_PER_REQUEST:
            raise serializers.ValidationError(
                f"Too many device ids [{len(device_ids)=}, {max_devices=}]"
            )
        return device_ids

    def validate_context(self, context):
        if not isinstance(context, dict):
            raise serializers.ValidationError("Context must be a dictionary")
        return context


class NotificationCreateResponseSerializer(serializers.Serializer):
    total_device_count = serializers.IntegerField()
    total_create_count = serializers.IntegerField()
    total_token_count = serializers.IntegerField()
    failed_token_count = serializers.IntegerField()
    missing_device_ids = serializers.ListField(
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
