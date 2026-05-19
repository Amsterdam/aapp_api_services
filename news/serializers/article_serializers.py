from rest_framework import serializers

from news.models import NewsArticle, NewsArticleImage


class NewsArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticleImage
        fields = ["url", "width", "height"]


class NewsArticleResponseSerializer(serializers.ModelSerializer):
    images = NewsArticleImageSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "title",
            "images",
            "publication_datetime",
            "modification_datetime",
        ]


class NewsArticleTransformSerializer(serializers.Serializer):
    """Serializer for validating and transforming news article data during ETL process"""

    id = serializers.CharField()
    title = serializers.CharField()
    body = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True)
    intro = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(allow_blank=True)
    district = serializers.CharField(allow_blank=True, allow_null=True)
    url = serializers.URLField(allow_blank=True)
    created = serializers.DateTimeField(required=False)
    modified = serializers.DateTimeField(required=False)
    publicationDate = serializers.DateTimeField()
    expirationDate = serializers.DateTimeField(required=False)
    image_url = serializers.URLField(required=False, allow_blank=True)
