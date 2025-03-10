from rest_framework import serializers

from construction_work.models.manage_models import WarningImage, WarningMessage
from construction_work.serializers.project_serializers import (
    WarningMessageForManagementSerializer,
)
from construction_work.utils.bool_utils import string_to_bool
from core.services.image_set import ImageSetService


class WarningImageCreateUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()


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
            image_set_id = validated_data["warning_image"]["id"]
            warning_image = self.construct_warning_image(image_set_id)
            new_warning.warningimage_set.add(warning_image)

        return new_warning

    def update(self, warning: WarningMessage, validated_data):
        warning.title = validated_data.get("title", warning.title)
        warning.body = validated_data.get("body", warning.body)
        warning.save()

        warning.warningimage_set.update(warning=None)
        if validated_data.get("warning_image"):
            image_set_id = validated_data["warning_image"]["id"]
            warning_image = self.construct_warning_image(image_set_id)
            warning.warningimage_set.add(warning_image)
            warning.save()

        return warning

    @staticmethod
    def construct_warning_image(image_set_id):
        image_data = ImageSetService().get(image_set_id)
        warning_image = WarningImage(image_set_id=image_set_id)
        warning_image.save()
        for variant in image_data["variants"]:
            warning_image.image_set.create(
                image=variant["image"],
                width=variant["width"],
                height=variant["height"],
                description=image_data["description"],
                warning_image=warning_image,
            )
        return warning_image


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
