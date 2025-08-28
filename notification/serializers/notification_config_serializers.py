from rest_framework import serializers

from notification.models import (
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
)


class NotificationPushTypeDisabledSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPushTypeDisabled
        fields = ["notification_type"]


class NotificationPushTypeDisabledListSerializer(
    NotificationPushTypeDisabledSerializer
):
    def to_representation(self, instance):
        return instance.notification_type


class NotificationPushModuleDisabledSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPushModuleDisabled
        fields = ["module_slug"]


class NotificationPushModuleDisabledListSerializer(
    NotificationPushModuleDisabledSerializer
):
    def to_representation(self, instance):
        return instance.module_slug
