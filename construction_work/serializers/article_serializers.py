from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from construction_work.models import Article
from construction_work.utils.model_utils import create_id_dict


class MetaIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()


class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer"""

    meta_id = serializers.SerializerMethodField()

    class Meta:
        model = Article
        exclude = ["type"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj: Article) -> dict:
        return create_id_dict(obj)


class ArticleMinimalSerializer(ArticleSerializer):
    """Article serializer with minimal data"""

    class Meta:
        model = Article
        fields = ["meta_id", "modification_date"]


class RecentArticlesIdDateSerializer(serializers.Serializer):
    meta_id = MetaIdSerializer()
    modification_date = serializers.DateTimeField()


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

    def get_meta_id(self, obj):
        return create_id_dict(obj)

    def get_images(self, obj):
        images = []
        if obj.image:
            images.append(obj.image)
        return images

    # NOTE: somehow, somewhere the datetime object is translated to string
    def get_publication_date(self, obj):
        return obj.publication_date
