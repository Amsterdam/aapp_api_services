from rest_framework import serializers

from news.models import LiveblogNotification, NewsArticle


class NotificationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveblogNotification
        fields = "__all__"


class NotificationRequestSerializer(serializers.ModelSerializer):
    article_foreign_id = serializers.SlugRelatedField(
        queryset=NewsArticle.objects.all(),
        slug_field="foreign_id",
        source="article",
    )

    class Meta:
        model = LiveblogNotification
        fields = ["article_foreign_id"]
