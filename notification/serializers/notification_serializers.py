from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.services.image_set import ImageSetService
from notification.models import (
    Notification,
    NotificationLast,
)


class NotificationImageSourceSerializer(serializers.Serializer):
    uri = serializers.URLField(source="image")
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class NotificationImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    description = serializers.CharField(required=False)
    sources = NotificationImageSourceSerializer(many=True, source="variants")


class NotificationContextSerializer(serializers.Serializer):
    linkSourceid = serializers.CharField(allow_null=True, required=False)
    type = serializers.CharField()
    module_slug = serializers.CharField()
    url = serializers.CharField(allow_null=True, required=False)
    deeplink = serializers.CharField(allow_null=True, required=False)

    def validate(self, data):
        if data.get("url") and data.get("deeplink"):
            raise serializers.ValidationError(
                "url and deeplink cannot both be set. Please choose one or the other."
            )
        return data


class NotificationResultSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    context = serializers.SerializerMethodField()

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
    def get_image(self, obj: Notification) -> dict | None:
        if obj.image is None:
            return None

        image_set_data = ImageSetService().get(obj.image)
        return NotificationImageSerializer(image_set_data).data

    @extend_schema_field(NotificationContextSerializer)
    def get_context(self, obj: Notification) -> dict:
        context_data = obj.context or {
            "type": obj.notification_type,
            "module_slug": obj.module_slug,
        }

        serializer = NotificationContextSerializer(data=context_data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["is_read"]

    def to_representation(self, instance):
        return NotificationResultSerializer(context=self.context).to_representation(
            instance
        )


class NotificationLastResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLast
        fields = ["notification_scope", "last_create"]


class NotificationLastRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLast
        fields = ["module_slug"]


class NotificationTypeSerializer(serializers.Serializer):
    type = serializers.CharField()
    description = serializers.CharField()


class ModuleNotificationTypeSerializer(serializers.Serializer):
    module = serializers.CharField()
    description = serializers.CharField()
    types = NotificationTypeSerializer(many=True)
