import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from construction_work.models.manage_models import Image
from construction_work.utils.image_utils import SCALED_IMAGE_FORMAT, scale_image


class ImagePublicSerializer(serializers.ModelSerializer):
    """Image public serializer"""

    uri = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["uri", "width", "height"]

    def get_uri(self, obj: Image) -> str:
        """Get URI"""
        media_url: str = self.context.get("media_url", "")
        media_url = media_url.rstrip("/")
        if not media_url:
            return None
        return f"{media_url}/{obj.image.name}"


class ImageCreateSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    description = serializers.CharField(required=False)

    def create(self, validated_data):
        image_file = validated_data["image"]
        description = validated_data.get("description")

        image_ids = []
        new_file_name = uuid.uuid4()

        scaled_images = scale_image(image_file)
        for size, img_io in scaled_images:
            image_obj = Image(description=description)
            image_content = ContentFile(img_io.read())
            image_obj.image.save(
                f"{new_file_name}_{size}.{SCALED_IMAGE_FORMAT.lower()}",
                image_content,
                save=False,
            )
            image_obj.save()
            image_ids.append(image_obj.pk)
        return image_ids
