import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from construction_work.models.manage_models import Image, WarningImage, WarningMessage
from construction_work.serializers.project_serializers import (
    WarningMessageForManagementSerializer,
)
from construction_work.utils.bool_utils import string_to_bool
from construction_work.utils.image_utils import SCALED_IMAGE_FORMAT, scale_image


class WarningImageCreateUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    description = serializers.CharField()


class WarningMessageCreateUpdateSerializer(serializers.Serializer):
    """Validate incoming warning message serializer"""

    title = serializers.CharField(required=True)
    body = serializers.CharField(required=True)
    warning_image = WarningImageCreateUpdateSerializer(required=False)
    send_push_notification = serializers.BooleanField(required=True)

    def validate_send_push_notification(self, value):
        try:
            send_push_notification = string_to_bool(value)
            return send_push_notification
        except ValueError as e:
            return serializers.ValidationError(str(e))

    def create(self, validated_data):
        new_warning = WarningMessage.objects.create(
            title=validated_data.get("title"),
            body=validated_data.get("body"),
            project=self.context.get("project"),
            project_manager=self.context.get("project_manager"),
        )

        if validated_data.get("warning_image"):
            warning_image = WarningImage.objects.get(
                id=validated_data["warning_image"]["id"]
            )
            new_warning.warningimage_set.add(warning_image)

        return new_warning

    def update(self, instance: WarningMessage, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.body = validated_data.get("body", instance.body)
        instance.save()

        instance.warningimage_set.update(warning=None)
        if validated_data.get("warning_image"):
            warning_image = WarningImage.objects.get(
                id=validated_data["warning_image"]["id"]
            )
            warning_image.images.all().update(
                description=validated_data["warning_image"]["description"]
            )
            warning_image.warning = instance
            warning_image.save()

        return instance


class WarningMessageWithNotificationResultSerializer(
    WarningMessageForManagementSerializer
):
    push_code = serializers.SerializerMethodField()
    push_message = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager", "author_email"]

    def get_push_code(self, _) -> bool:
        """Push request status code"""
        return self.context.get("push_code")

    def get_push_message(self, _) -> str:
        """Why was push request (not) ok"""
        return self.context.get("push_message")


class WarningImageSerializer(serializers.ModelSerializer):
    """Warning image serializer"""

    class Meta:
        model = WarningImage
        fields = "__all__"


class PublisherAssignProjectSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()


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
