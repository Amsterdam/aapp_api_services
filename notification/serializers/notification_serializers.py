from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.services.image_set import ImageSetService
from notification.models import Notification


class NotificationImageSourceSerializer(serializers.Serializer):
    uri = serializers.URLField(source="image")
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class NotificationImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    description = serializers.CharField(required=False)
    sources = NotificationImageSourceSerializer(many=True, source="variants")


class NotificationResultSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

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

    @extend_schema_field(NotificationImageSerializer)
    def get_image(self, obj: Notification) -> dict:
        if obj.image is None:
            return None

        image_set_data = ImageSetService().get(obj.image)
        return NotificationImageSerializer(image_set_data).data


class NotificationCreateSerializer(serializers.ModelSerializer):
    device_ids = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = Notification
        fields = [
            "title",
            "body",
            "module_slug",
            "context",
            "created_at",
            "device_ids",
            "notification_type",
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
