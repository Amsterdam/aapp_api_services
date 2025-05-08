import hashlib
import io
import logging
import uuid

import requests
from django.core.files.base import ContentFile
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from core.utils.image_utils import SCALED_IMAGE_FORMAT, scale_image
from image.models import ImageSet, ImageVariant

logger = logging.getLogger(__name__)


class ImageSetBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageSet
        abstract = True

    @transaction.atomic
    def create_set(self, image_file, validated_data):
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


class ImageSetRequestSerializer(ImageSetBaseSerializer):
    image = serializers.ImageField(write_only=True)

    class Meta:
        model = ImageSet
        fields = ["id", "image", "identifier", "description"]

    def create(self, validated_data):
        image_file = validated_data.pop("image")
        return self.create_set(image_file, validated_data)


class ImageSetFromUrlRequestSerializer(ImageSetBaseSerializer):
    url = serializers.URLField(write_only=True)

    class Meta:
        model = ImageSet
        fields = ["id", "url", "description"]

    def create(self, validated_data):
        url = validated_data.pop("url")
        response = requests.get(url)
        response.raise_for_status()
        image_file = io.BytesIO(response.content)
        try:
            image_file.seek(0)
            Image.open(image_file).verify()
            image_file.seek(0)
        except UnidentifiedImageError:
            raise serializers.ValidationError(
                "Provided URL does not contain a valid image."
            )
        validated_data["identifier"] = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.create_set(image_file, validated_data)


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
