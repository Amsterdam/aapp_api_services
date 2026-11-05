from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import ChoiceField

from core.serializers.image_serializers import ImageSerializer
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


def serialize_image_sets(obj):
    image_sets = {}
    image_sources = sorted(obj.images.all(), key=lambda image_source: image_source.pk)
    for image_source in image_sources:
        image_set_id = image_source.foreign_id or image_source.pk
        image_set = image_sets.setdefault(
            image_set_id,
            {
                "id": image_set_id,
                "sources": [],
                "alt": image_source.alt,
                "description": image_source.description,
            },
        )
        image_set["sources"].append(
            {
                "uri": image_source.uri,
                "width": image_source.width,
                "height": image_source.height,
            }
        )

    return ImageSerializer(image_sets.values(), many=True).data


class NewsArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticleImage
        fields = ["uri", "width", "height"]


class NewsArticleImageFieldsMixin:
    @extend_schema_field(ImageSerializer(allow_null=True))
    def get_image(self, obj):
        images = serialize_image_sets(obj)
        return images[0] if images else None


class NewsArticleLiveblogItemSerializer(
    NewsArticleImageFieldsMixin, serializers.ModelSerializer
):
    image = serializers.SerializerMethodField()

    class Meta:
        model = LiveBlogItem
        fields = ["id", "creation_datetime", "title", "body", "message_order", "image"]


class NewsArticleListResponseSerializer(
    NewsArticleImageFieldsMixin, serializers.ModelSerializer
):
    images = NewsArticleImageSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "title",
            "images",
            "image",
            "publication_datetime",
            "modification_datetime",
            "is_liveblog",
            "is_active_liveblog",
        ]


class NewsArticleDetailResponseSerializer(
    NewsArticleImageFieldsMixin, serializers.ModelSerializer
):
    images = NewsArticleImageSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
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
