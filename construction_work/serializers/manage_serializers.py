from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from construction_work.models.manage_models import (
    ProjectManager,
    WarningImage,
    WarningMessage,
)
from construction_work.models.project_models import Project
from construction_work.serializers.article_serializers import ArticleSerializer
from construction_work.serializers.project_serializers import (
    ProjectExtendedWithFollowersSerializer,
    ProjectManagerNameEmailSerializer,
    WarningMessageSerializer,
)
from construction_work.utils.bool_utils import string_to_bool
from construction_work.utils.query_utils import (
    get_recent_articles_of_project,
    get_recent_warnings_of_project,
)
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


class WarningMessageWithNotificationResultSerializer(WarningMessageSerializer):
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


class PublisherAssignProjectSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()


class ImageCreateSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    description = serializers.CharField(required=False)


class ProjectListForManageSerializer(ProjectExtendedWithFollowersSerializer):
    publishers = serializers.SerializerMethodField()
    warning_count = serializers.SerializerMethodField()
    article_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "foreign_id",
            "title",
            "subtitle",
            "image",
            "creation_date",
            "publishers",
            "warning_count",
            "article_count",
        ]

    @extend_schema_field(ProjectManagerNameEmailSerializer)
    def get_publishers(self, obj: Project) -> list:
        managers = obj.projectmanager_set.all()
        serializer = ProjectManagerNameEmailSerializer(instance=managers, many=True)
        return serializer.data

    def get_warning_count(self, obj: Project) -> int:
        warning_count = obj.warningmessage_set.count()
        return warning_count

    def get_article_count(self, obj: Project) -> int:
        article_count = obj.article_set.count()
        return article_count


class ProjectDetailsForManagementSerializer(ProjectListForManageSerializer):
    """Project details for warning management"""

    warnings = serializers.SerializerMethodField()
    articles = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "foreign_id",
            "url",
            "title",
            "subtitle",
            "creation_date",
            "image",
            "publishers",
            "warnings",
            "articles",
            "followers",
        ]

    @extend_schema_field(WarningMessageSerializer)
    def get_warnings(self, obj: Project) -> list:
        media_url = self.context.get("media_url")
        article_max_age = self.context.get("article_max_age", 10000)
        warnings = get_recent_warnings_of_project(
            obj,
            article_max_age,
            WarningMessageSerializer,
            context={"media_url": media_url},
        )
        return warnings

    @extend_schema_field(ArticleSerializer)
    def get_articles(self, obj: Project) -> list:
        article_max_age = self.context.get("article_max_age", 10000)
        articles = get_recent_articles_of_project(
            obj, article_max_age, ArticleSerializer
        )
        return articles


class ProjectManagerWithProjectsSerializer(serializers.ModelSerializer):
    """Project managers serializer"""

    projects = serializers.SerializerMethodField()

    class Meta:
        model = ProjectManager
        fields = "__all__"

    def get_projects(self, obj: ProjectManager) -> list[int]:
        """Get projects"""
        project_ids = [project.id for project in obj.projects.all()]
        return project_ids


class ProjectManagerCreateResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectManager
        fields = ["id", "name", "email"]
