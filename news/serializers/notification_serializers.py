from rest_framework import serializers

from news.models import LiveblogNotification


class NotificationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveblogNotification
        fields = "__all__"


class NotificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveblogNotification
        fields = ["article"]
