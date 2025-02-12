import uuid

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from core.utils.image_utils import SCALED_IMAGE_FORMAT, scale_image
from image.models import ImageSet, ImageVariant


class ImageSetRequestSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)

    class Meta:
        model = ImageSet
        fields = ["description", "image"]

    @transaction.atomic
    def create(self, validated_data):
        image_file = validated_data.pop("image")
        scaled = scale_image(image_file)
        image_small = self._get_image_variant(scaled, "small")
        image_medium = self._get_image_variant(scaled, "medium")
        image_large = self._get_image_variant(scaled, "large")
        return ImageSet.objects.create(
            image_small=image_small,
            image_medium=image_medium,
            image_large=image_large,
            **validated_data,
        )

    def _get_image_variant(self, scaled_images, key) -> ImageVariant:
        filename = f"{key}-{uuid.uuid4()}.{SCALED_IMAGE_FORMAT}"
        content_file = ContentFile(scaled_images[key].read(), filename)
        return ImageVariant.objects.create(image=content_file)


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
        fields = ["id", "description", "variants"]

    def get_variants(self, obj: ImageSet) -> list:
        variants = [
            obj.image_small,
            obj.image_medium,
            obj.image_large,
        ]
        return ImageVariantSerializer(variants, many=True).data
