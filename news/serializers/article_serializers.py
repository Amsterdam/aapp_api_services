from rest_framework import serializers
from rest_framework.fields import ChoiceField

from news.models import (
    ARTICLE_TYPE_CHOICES,
    DISTRICT_TYPE_CHOICES,
    LiveBlogItem,
    NewsArticle,
    NewsArticleImage,
)


class NewsArticleRequestSerializer(serializers.Serializer):
    type = ChoiceField(choices=ARTICLE_TYPE_CHOICES)
    district = ChoiceField(choices=DISTRICT_TYPE_CHOICES, required=False)

    def validate(self, attrs):
        is_district_type = attrs["type"] == "district"
        has_district = attrs.get("district") is not None

        if is_district_type != has_district:
            raise serializers.ValidationError(
                {"district": "Required only when type is 'district'."}
            )
        return attrs


class NewsArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticleImage
        fields = ["uri", "width", "height"]


class NewsArticleLiveblogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveBlogItem
        fields = ["id", "creation_datetime", "title", "body", "message_order"]


class NewsArticleListResponseSerializer(serializers.ModelSerializer):
    images = NewsArticleImageSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "title",
            "images",
            "publication_datetime",
            "modification_datetime",
            "is_liveblog",
            "is_active_liveblog",
        ]


class NewsArticleDetailResponseSerializer(serializers.ModelSerializer):
    images = NewsArticleImageSerializer(many=True, read_only=True)
    liveblog_items = NewsArticleLiveblogItemSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        exclude = ["deleted"]


class NewsArticleTransformSerializer(serializers.Serializer):
    """
    Serializer for validating and transforming news article data during ETL process,
    not directly tied to the NewsArticle model. These fields are designed to match the
    expected input data structure from the source system.
    """

    id = serializers.CharField()
    title = serializers.CharField()
    body = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True)
    intro = serializers.CharField(required=False, allow_blank=True)
    in_all_news = serializers.BooleanField(required=False)
    is_highlight = serializers.BooleanField(required=False)
    is_liveblog = serializers.BooleanField(required=False)
    is_district = serializers.BooleanField(required=False)
    district = serializers.CharField(allow_blank=True, allow_null=True)
    url = serializers.URLField(allow_blank=True)
    created = serializers.DateTimeField(required=False)
    modified = serializers.DateTimeField(required=False)
    publicationDate = serializers.DateTimeField()
    expirationDate = serializers.DateTimeField(required=False)
    image_url = serializers.URLField(required=False, allow_blank=True)
