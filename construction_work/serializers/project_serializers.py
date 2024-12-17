from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from construction_work.models.manage_models import (
    ProjectManager,
    WarningImage,
    WarningMessage,
)
from construction_work.models.project_models import (
    Project,
    ProjectContact,
    ProjectImage,
    ProjectImageSource,
    ProjectTimelineItem,
)
from construction_work.serializers.article_serializers import (
    ArticleMinimalSerializer,
    ArticleSerializer,
    RecentArticlesIdDateSerializer,
)
from construction_work.serializers.general_serializers import MetaIdSerializer
from construction_work.serializers.image_serializer import ImagePublicSerializer
from construction_work.serializers.iprox_serializer import (
    IproxCoordinatesSerializer,
    IproxImageSerializer,
    IproxProjectSectionsSerializer,
    IproxProjectTimelineSerializer,
)
from construction_work.utils.bool_utils import string_to_bool
from construction_work.utils.geo_utils import calculate_distance
from construction_work.utils.model_utils import create_id_dict
from construction_work.utils.query_utils import (
    get_recent_articles_of_project,
    get_recent_warnings_of_project,
)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    Special ModelSerializer used for enabling the search function.
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ProjectImageSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImageSource
        exclude = ["image", "id"]


class ProjectImageSerializer(serializers.ModelSerializer):
    sources = ProjectImageSourceSerializer(many=True)

    class Meta:
        model = ProjectImage
        exclude = ["parent"]


class ProjectExtendedSerializer(DynamicFieldsModelSerializer):
    """Project list serializer"""

    meter = serializers.SerializerMethodField()
    followed = serializers.SerializerMethodField()
    recent_articles = serializers.SerializerMethodField()
    image = ProjectImageSerializer()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "subtitle",
            "image",
            "followed",
            "meter",
            "recent_articles",
        ]

    def get_meter(self, obj: Project) -> int:
        """Calculate distance from given coordinates to project coordinates"""
        lat = self.context.get("lat")
        lon = self.context.get("lon")
        if obj is None or lat is None or lon is None:
            return None

        cords_1 = (float(lat), float(lon))
        project_coordinates = {"lat": obj.coordinates_lat, "lon": obj.coordinates_lon}
        if project_coordinates is None:
            return None
        cords_2 = (project_coordinates.get("lat"), project_coordinates.get("lon"))
        if None in cords_2 or (cords_2 == (0, 0)):
            return None
        meter = calculate_distance(cords_1, cords_2)
        return meter

    def get_followed(self, obj: Project) -> bool:
        """Check if project is being followed by given device"""
        followed_projects_ids = self.context.get("followed_projects_ids", [])
        return obj.pk in followed_projects_ids

    @extend_schema_field(RecentArticlesIdDateSerializer)
    def get_recent_articles(self, obj: Project) -> list:
        """Get recent articles and warnings"""
        recent_news = []

        for article in getattr(obj, "recent_articles", []):
            news_dict = {
                "meta_id": create_id_dict(article),
                "modification_date": str(article.modification_date),
            }
            recent_news.append(news_dict)

        for warning in getattr(obj, "recent_warnings", []):
            news_dict = {
                "meta_id": create_id_dict(warning),
                "modification_date": str(warning.modification_date),
            }
            recent_news.append(news_dict)

        return recent_news


class ProjectContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContact
        exclude = ["project"]


class ProjectExtendedWithFollowersSerializer(ProjectExtendedSerializer):
    """Project details serializer"""

    followers = serializers.SerializerMethodField()
    recent_articles = serializers.SerializerMethodField()
    meter = serializers.SerializerMethodField()
    followed = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()

    contacts = ProjectContactSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "meter",
            "followed",
            "recent_articles",
            "image",
            "followers",
            "foreign_id",
            "active",
            "last_seen",
            "title",
            "subtitle",
            "contacts",
            "url",
            "timeline",
            "sections",
            "coordinates",
            "creation_date",
            "modification_date",
            "publication_date",
            "expiration_date",
        ]

    def get_followers(self, obj: Project) -> int:
        """Get amount of followers of project"""
        return obj.device_set.count()

    @extend_schema_field(ArticleSerializer(many=True))
    def get_recent_articles(self, obj: Project) -> list:
        """Get recent articles and warnings"""
        article_max_age = self.context.get("article_max_age", 3)
        media_url = self.context.get("media_url", "")
        start_date = timezone.now() - timedelta(days=article_max_age)

        # Get recent articles
        recent_articles = obj.article_set.filter(publication_date__gte=start_date)
        article_serializer = ArticleSerializer(recent_articles, many=True)

        # Get recent warnings
        recent_warnings = obj.warningmessage_set.filter(
            publication_date__gte=start_date
        )
        warning_serializer = WarningMessageForManagementSerializer(
            recent_warnings, many=True, context={"media_url": media_url}
        )

        # Combine articles and warnings
        all_items = article_serializer.data + warning_serializer.data
        # Sort combined list by modification_date descending
        all_items.sort(key=lambda x: x.get("modification_date", ""), reverse=True)
        return all_items

    @extend_schema_field(IproxProjectSectionsSerializer)
    def get_sections(self, obj):
        response = {key: [] for key in ("where", "what", "when", "work", "contact")}
        for section in obj.sections.all():
            response[section.type].append(
                {
                    "body": section.body,
                    "title": section.title,
                    "links": [
                        {"url": link["url"], "label": link["label"]}
                        for link in section.links.values()
                    ],
                }
            )
        return response

    @extend_schema_field(IproxProjectTimelineSerializer)
    def get_timeline(self, obj):
        items = self.get_timeline_items(obj.timeline_items.all())
        if not items:
            return None

        response = {
            "intro": obj.timeline_intro,
            "title": obj.timeline_title,
            "items": items,
        }
        return response

    def get_timeline_items(self, item_ids):
        """
        This is a recursive function to build the timeline items tree
        """
        timeline_items = ProjectTimelineItem.objects.filter(id__in=item_ids)
        response = []
        for item in timeline_items:
            items = self.get_timeline_items(item.items.all())
            response.append(
                {
                    "title": item.title,
                    "body": item.body,
                    "collapsed": item.collapsed,
                    "items": items,
                }
            )
        return response

    @extend_schema_field(IproxCoordinatesSerializer)
    def get_coordinates(self, obj: Project) -> dict:
        """Get coordinates"""
        return {
            "lat": obj.coordinates_lat,
            "lon": obj.coordinates_lon,
        }


class ProjectManagerNameEmailSerializer(serializers.ModelSerializer):
    """Project manager serializer"""

    class Meta:
        model = ProjectManager
        fields = ["name", "email"]


class ProjectManagerCreateResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectManager
        fields = ["id", "name", "email"]


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


class WarningMessageWithImagesSerializer(serializers.ModelSerializer):
    """Warning message with images serializer"""

    meta_id = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj: WarningMessage) -> dict:
        return create_id_dict(obj)

    @extend_schema_field(IproxImageSerializer(many=True))
    def get_images(self, obj: WarningMessage):
        """Get images"""
        media_url = self.context.get("media_url", "")
        images = []
        for warning_image in obj.warningimage_set.all():
            image_serializer = ImagePublicSerializer(
                warning_image.images.all(),
                many=True,
                context={"media_url": media_url},
            )
            sources = image_serializer.data

            first_image = warning_image.images.first()
            image = {
                "id": warning_image.pk,
                "sources": sources,
                "landscape": bool(first_image.width > first_image.height),
                "alternativeText": first_image.description,
            }
            images.append(image)
        return images


class WarningMessageForManagementSerializer(WarningMessageWithImagesSerializer):
    """Warning message serializer for management interface"""

    publisher = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager", "author_email"]

    @extend_schema_field(ProjectManagerNameEmailSerializer)
    def get_publisher(self, obj: WarningMessage):
        serializer = ProjectManagerNameEmailSerializer(obj.project_manager)
        return serializer.data


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

    @extend_schema_field(WarningMessageForManagementSerializer)
    def get_warnings(self, obj: Project) -> list:
        media_url = self.context.get("media_url")
        article_max_age = self.context.get("article_max_age", 10000)
        warnings = get_recent_warnings_of_project(
            obj,
            article_max_age,
            WarningMessageForManagementSerializer,
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


class WarningMessageMinimalSerializer(serializers.ModelSerializer):
    """Waring message serializer with meta id field"""

    meta_id = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        fields = ["meta_id", "modification_date"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj: WarningMessage) -> dict:
        return obj.get_id_dict()


class ProjectFollowedArticlesSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source="pk")
    recent_articles = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["project_id", "recent_articles"]

    @extend_schema_field(ArticleMinimalSerializer)
    def get_recent_articles(self, obj: Project) -> list:
        now = timezone.now()
        start_date = now - timedelta(days=settings.ARTICLE_MAX_AGE)

        recent_articles = obj.article_set.filter(publication_date__gte=start_date)
        article_serializer = ArticleMinimalSerializer(recent_articles, many=True)

        recent_warnings = obj.warningmessage_set.filter(
            publication_date__gte=start_date
        )
        warning_serializer = WarningMessageMinimalSerializer(recent_warnings, many=True)

        all_items = article_serializer.data + warning_serializer.data
        all_items.sort(key=lambda x: x.get("modification_date", ""), reverse=True)
        return all_items


class FollowProjectPostDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class WarningMessageListSerializer(serializers.ModelSerializer):
    """
    Serializer for WarningMessage model in list view.
    """

    meta_id = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    title = serializers.CharField()
    publication_date = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        fields = ["meta_id", "images", "title", "publication_date"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj):
        return create_id_dict(obj)

    def get_images(self, obj):
        images = []
        warning_images = obj.warningimage_set.prefetch_related("images")
        for warning_image in warning_images:
            image_serializer = ImagePublicSerializer(
                warning_image.images.all(), many=True, context=self.context
            )
            images.append({"id": warning_image.pk, "sources": image_serializer.data})
        return images

    # NOTE: somehow, somewhere the datetime object is translated to string
    def get_publication_date(self, obj):
        return obj.publication_date


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
