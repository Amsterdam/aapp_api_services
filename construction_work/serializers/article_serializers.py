from datetime import datetime

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from construction_work.models.article_models import Article
from construction_work.models.manage_models import WarningImage, WarningMessage
from construction_work.serializers.general_serializers import (
    ImagePublicSerializer,
    IproxImageSerializer,
    MetaIdSerializer,
    serialize_image_variants,
)
from construction_work.utils.model_utils import create_id_dict


class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer"""

    meta_id = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        exclude = ["type"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj: Article) -> dict:
        return create_id_dict(obj)

    @extend_schema_field(IproxImageSerializer(allow_null=True))
    def get_image(self, obj: Article):
        return serialize_image_variants(list(obj.images.all()))


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer for Article model in list view.
    """

    meta_id = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
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

    @extend_schema_field(IproxImageSerializer(many=True))
    def get_images(self, obj: Article):
        return serialize_image_variants(list(obj.images.all()))

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
