from rest_framework import serializers

from notification.models import (
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
)


class NotificationPushEnabledSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPushTypeDisabled
        fields = ["notification_type"]


class NotificationPushEnabledListSerializer(NotificationPushEnabledSerializer):
    def to_representation(self, instance):
        return instance.notification_type


class NotificationPushModuleEnabledSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPushModuleDisabled
        fields = ["module_slug"]


class NotificationPushModuleEnabledListSerializer(
    NotificationPushModuleEnabledSerializer
):
    def to_representation(self, instance):
        return instance.module_slug
