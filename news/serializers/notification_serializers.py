import logging

from rest_framework import serializers

from news.models.article_models import LiveblogNotification

logger = logging.getLogger(__name__)


class NotificationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveblogNotification
        fields = "__all__"
