from rest_framework import serializers

from news.models import NewsArticle, NewsArticleImage


class NewsArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticleImage
        fields = ["url", "width", "height"]


class NewsArticleListResponseSerializer(serializers.ModelSerializer):
    images = NewsArticleImageSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = ["id", "title", "images", "publication_date", "modification_date"]
