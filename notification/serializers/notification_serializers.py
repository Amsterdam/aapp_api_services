from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.services.image_set import ImageSetService
from notification.exceptions import (
    ImageSetNotFoundError,
    ScheduledNotificationDuplicateIdentifierError,
    ScheduledNotificationIdentifierError,
    ScheduledNotificationInPastError,
)
from notification.models import (
    Device,
    Notification,
    NotificationLast,
    ScheduledNotification,
)


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
    def get_image(self, obj: Notification) -> dict | None:
        if obj.image is None:
            return None

        image_set_data = ImageSetService().get(obj.image)
        return NotificationImageSerializer(image_set_data).data


class NotificationCreateSerializer(serializers.ModelSerializer):
    device_ids = serializers.ListField(child=serializers.CharField(), write_only=True)
    make_push = serializers.BooleanField(default=True, write_only=True)

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
            "make_push",
        ]

    def validate_device_ids(self, device_ids):
        if len(device_ids) != len(set(device_ids)):
            raise serializers.ValidationError("Duplicate device ids found in input")
        return device_ids

    def validate_image(self, image_id):
        if not ImageSetService().exists(image_id):
            raise ImageSetNotFoundError()
        return image_id

    def validate_context(self, context):
        if not isinstance(context, dict):
            raise serializers.ValidationError("Context must be a dictionary")
        return context


class ScheduledNotificationDetailSerializer(NotificationCreateSerializer):
    scheduled_for = serializers.DateTimeField()
    device_ids = serializers.SlugRelatedField(
        many=True,
        queryset=Device.objects.all(),
        slug_field="external_id",
        source="devices",
    )

    class Meta:
        model = ScheduledNotification
        fields = [
            "title",
            "body",
            "module_slug",
            "context",
            "created_at",
            "device_ids",
            "notification_type",
            "image",
            "scheduled_for",
            "expires_at",
        ]

    def validate_scheduled_for(self, scheduled_date):
        if scheduled_date < timezone.now():
            raise ScheduledNotificationInPastError()
        return scheduled_date


class ScheduledNotificationSerializer(ScheduledNotificationDetailSerializer):
    identifier = serializers.CharField()

    class Meta:
        model = ScheduledNotification
        fields = ScheduledNotificationDetailSerializer.Meta.fields + [
            "identifier",
        ]

    def validate(self, attrs):
        if attrs.get("expires_at") and attrs["expires_at"] <= attrs["scheduled_for"]:
            raise serializers.ValidationError("Expires at must be after scheduled for")
        return attrs

    def validate_identifier(self, identifier):
        module_slug = self.initial_data.get("module_slug")
        if not identifier:
            raise serializers.ValidationError("Identifier is required.")
        if module_slug and not identifier.startswith(module_slug):
            raise ScheduledNotificationIdentifierError()
        if ScheduledNotification.objects.filter(identifier=identifier).exists():
            raise ScheduledNotificationDuplicateIdentifierError()
        return identifier


class NotificationCreateResponseSerializer(serializers.Serializer):
    total_device_count = serializers.IntegerField()
    total_token_count = serializers.IntegerField()
    total_enabled_count = serializers.IntegerField()
    failed_token_count = serializers.IntegerField()


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
