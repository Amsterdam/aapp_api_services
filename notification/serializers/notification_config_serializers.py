from rest_framework import serializers

from notification.models import (
    NotificationPushServiceEnabled,
    NotificationPushTypeEnabled,
)


class NotificationPushEnabledSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPushTypeEnabled
        fields = ["notification_type"]


class NotificationPushEnabledListSerializer(NotificationPushEnabledSerializer):
    def to_representation(self, instance):
        return instance.notification_type


class NotificationPushServiceEnabledSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPushServiceEnabled
        fields = ["service_name"]


class NotificationPushServiceEnabledListSerializer(
    NotificationPushServiceEnabledSerializer
):
    def to_representation(self, instance):
        return instance.service_name
