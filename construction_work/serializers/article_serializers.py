from datetime import datetime

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from construction_work.models.article_models import (
    Article,
    ArticleImage,
    ArticleImageSource,
)
from construction_work.models.manage_models import WarningImage, WarningMessage
from construction_work.serializers.general_serializers import (
    ImagePublicSerializer,
    MetaIdSerializer,
)
from construction_work.utils.model_utils import create_id_dict


class ArticleImageSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleImageSource
        exclude = ["image", "id"]


class ArticleImageSerializer(serializers.ModelSerializer):
    sources = ArticleImageSourceSerializer(many=True)

    class Meta:
        model = ArticleImage
        exclude = ["parent"]


class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer"""

    meta_id = serializers.SerializerMethodField()
    image = ArticleImageSerializer()

    class Meta:
        model = Article
        exclude = ["type"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj: Article) -> dict:
        return create_id_dict(obj)


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer for Article model in list view.
    """

    meta_id = serializers.SerializerMethodField()
    images = ArticleImageSerializer(source="image")
    publication_date = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["meta_id", "images", "title", "publication_date"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj):
        return create_id_dict(obj)

    # NOTE: somehow, somewhere the datetime object is translated to string
    def get_publication_date(self, obj) -> datetime:
        return obj.publication_date

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get("images"):
            representation["images"] = [representation["images"]]
        else:
            representation["images"] = []
        return representation


class WarningImageSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    sources = ImagePublicSerializer(source="image_set", many=True)

    class Meta:
        model = WarningImage
        fields = ["id", "sources"]

    def get_id(self, obj) -> str:
        # We do not want to expose the id used by the construction_work service, but the id used by the image service
        return obj.image_set_id


class WarningMessageListSerializer(serializers.ModelSerializer):
    """
    Serializer for WarningMessage model in list view.
    """

    meta_id = serializers.SerializerMethodField()
    images = WarningImageSerializer(source="warningimage_set", many=True)
    title = serializers.CharField()
    publication_date = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        fields = ["meta_id", "images", "title", "publication_date"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj):
        return create_id_dict(obj)

    # NOTE: somehow, somewhere the datetime object is translated to string
    def get_publication_date(self, obj) -> datetime:
        return obj.publication_date
