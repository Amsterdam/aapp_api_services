import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from core.utils.image_utils import SCALED_IMAGE_FORMAT, scale_image
from notification.models import ImageSet, ImageVariant

RESOLUTIONS = {
    "firebase": (200, 200),
    "thumbnail": (400, 400),
    "large": (800, 800),
}


class ImageVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageVariant
        exclude = ["id"]


class ImageSetSerializer(serializers.ModelSerializer):
    firebase_image = ImageVariantSerializer()
    thumbnail_image = ImageVariantSerializer()
    large_image = ImageVariantSerializer()

    class Meta:
        model = ImageSet
        fields = "__all__"


class ImageSetRequestSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)

    class Meta:
        model = ImageSet
        fields = ["description", "image"]

    def create(self, validated_data):
        image_file = validated_data.pop("image")
        scaled = scale_image(image_file, RESOLUTIONS)
        firebase_variant = self.get_image_variant(scaled, "firebase")
        thumbnail_variant = self.get_image_variant(scaled, "thumbnail")
        large_variant = self.get_image_variant(scaled, "large")
        return ImageSet.objects.create(
            firebase_image=firebase_variant,
            thumbnail_image=thumbnail_variant,
            large_image=large_variant,
            **validated_data,
        )

    def get_image_variant(self, scaled_images, key) -> ImageVariant:
        filename = f"{key}-{uuid.uuid4()}.{SCALED_IMAGE_FORMAT}"
        content_file = ContentFile(scaled_images[key].read(), filename)
        return ImageVariant.objects.create(image=content_file)
