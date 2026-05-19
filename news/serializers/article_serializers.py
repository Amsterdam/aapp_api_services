from rest_framework import serializers
from rest_framework.fields import ChoiceField

from news.models import (
    ARTICLE_TYPE_CHOICES,
    DISTRICT_TYPE_CHOICES,
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
            raise serializers.ValidationError({
                "district": "Required only when type is 'district'."
            })
        return attrs


class NewsArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticleImage
        fields = ["url", "width", "height"]


class NewsArticleResponseSerializer(serializers.ModelSerializer):
    images = NewsArticleImageSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = ["id", "title", "images", "publication_date", "modification_date"]
