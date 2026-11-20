from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from image.models import ImageSet, ImageVariant
from image.services.image_set import create_from_upload, create_from_url


class ImageSetRequestSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)

    class Meta:
        model = ImageSet
        fields = ["id", "image", "identifier", "description"]

    def create(self, validated_data):
        image_file = validated_data.pop("image")
        return create_from_upload(image_file, validated_data)


class StrictURLField(serializers.URLField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class ImageSetFromUrlRequestSerializer(serializers.ModelSerializer):
    url = StrictURLField(write_only=True)

    class Meta:
        model = ImageSet
        fields = ["id", "url", "description"]

    def create(self, validated_data):
        url = validated_data.pop("url")
        return create_from_url(url, validated_data)


class ImageVariantSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ImageVariant
        exclude = ["id"]

    def get_image(self, obj):
        return obj.image_url


class ImageSetSerializer(serializers.ModelSerializer):
    variants = serializers.SerializerMethodField()

    class Meta:
        model = ImageSet
        fields = ["id", "identifier", "description", "variants"]

    @extend_schema_field(ImageVariantSerializer(many=True))
    def get_variants(self, obj: ImageSet) -> list:
        variants = [
            obj.image_small,
            obj.image_medium,
            obj.image_large,
        ]
        return ImageVariantSerializer(variants, many=True).data
