from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from construction_work.models import (
    Image,
    Notification,
    Project,
    ProjectManager,
    WarningMessage,
)
from construction_work.serializers.article_serializers import (
    ArticleMinimalSerializer,
    ArticleSerializer,
    RecentArticlesIdDateSerializer,
)
from construction_work.utils.geo_utils import calculate_distance
from construction_work.utils.model_utils import create_id_dict


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


class IproxImageSourceSerializer(serializers.Serializer):
    uri = serializers.CharField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class IproxImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sources = IproxImageSourceSerializer(many=True)
    aspectRatio = serializers.FloatField()
    alternativeText = serializers.CharField()


class ProjectExtendedSerializer(DynamicFieldsModelSerializer):
    """Project list serializer"""

    meter = serializers.SerializerMethodField()
    followed = serializers.SerializerMethodField()
    recent_articles = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

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
        project_coordinates = obj.coordinates
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

    @extend_schema_field(IproxImageSerializer)
    def get_image(self, obj: Project):
        """Get main image or first image from image list"""
        if obj.image:
            return obj.image
        if obj.images:
            return obj.images[0]
        return {}


class ProjectExtendedWithFollowersSerializer(ProjectExtendedSerializer):
    """Project details serializer"""

    followers = serializers.SerializerMethodField()
    recent_articles = serializers.SerializerMethodField()
    meter = serializers.SerializerMethodField()
    followed = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ["hidden"]

    def get_followers(self, obj: Project) -> int:
        """Get amount of followers of project"""
        return obj.device_set.count()

    @extend_schema_field(ArticleSerializer)
    def get_recent_articles(self, obj: Project) -> list:
        """Get recent articles and warnings"""
        article_max_age = self.context.get("article_max_age", 3)
        media_url = self.context.get("media_url", "")
        start_date = timezone.now() - timedelta(days=article_max_age)

        # Get recent articles
        recent_articles = obj.article_set.filter(publication_date__gte=start_date)
        article_serializer = ArticleSerializer(
            recent_articles,
            many=True,
        )

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


class ProjectManagerNameEmailSerializer(serializers.ModelSerializer):
    """Project manager serializer"""

    class Meta:
        model = ProjectManager
        fields = ["name", "email"]


class ProjectManagerCreateResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectManager
        fields = ["id", "name", "email"]


class ProjectManagerWithProjectsSerializer(serializers.ModelSerializer):
    """Project managers serializer"""

    projects = serializers.SerializerMethodField()

    class Meta:
        model = ProjectManager
        fields = "__all__"

    def get_projects(self, obj: ProjectManager) -> list:
        """Get projects"""
        project_ids = [project.id for project in obj.projects.all()]
        return project_ids


class ImagePublicSerializer(serializers.ModelSerializer):
    """Image public serializer"""

    uri = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["uri", "width", "height"]

    def get_uri(self, obj: Image):
        """Get URI"""
        media_url: str = self.context.get("media_url", "")
        media_url = media_url.rstrip("/")
        if not media_url:
            return None
        return f"{media_url}/{obj.image.name}"


class WarningMessageWithImagesSerializer(serializers.ModelSerializer):
    """Warning message with images serializer"""

    meta_id = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager"]

    def get_meta_id(self, obj: WarningMessage) -> dict:
        return create_id_dict(obj)

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
                "main": warning_image.is_main,
                "sources": sources,
                "landscape": bool(first_image.width > first_image.height),
                "alternativeText": first_image.description,
                "aspect_ratio": first_image.aspect_ratio,
            }
            images.append(image)
        return images


class WarningMessageForManagementSerializer(WarningMessageWithImagesSerializer):
    """Warning message serializer for management interface"""

    publisher = serializers.SerializerMethodField()
    is_pushed = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager", "author_email"]

    def get_publisher(self, obj: WarningMessage):
        serializer = ProjectManagerNameEmailSerializer(obj.project_manager)
        return serializer.data

    def get_is_pushed(self, obj: WarningMessage) -> bool:
        """Has the warning been pushed (before)"""
        return Notification.objects.filter(warning=obj).exists()


class WarningMessageMetaIdSerializer(serializers.ModelSerializer):
    """Waring message serializer with meta id field"""

    meta_id = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        fields = "__all__"

    def get_meta_id(self, obj: WarningMessage) -> dict:
        return obj.get_id_dict()


class WarningMessageMinimalSerializer(WarningMessageMetaIdSerializer):
    """Warning message serializer with minimal data"""

    class Meta:
        model = WarningMessage
        fields = ["meta_id", "modification_date"]


class ProjectFollowedArticlesSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source="pk")
    recent_articles = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["project_id", "recent_articles"]

    def get_recent_articles(self, obj: Project) -> list:
        article_max_age = self.context.get(settings.ARTICLE_MAX_AGE_PARAM, 3)
        now = timezone.now()
        start_date = now - timedelta(days=article_max_age)

        # Get recent articles
        recent_articles = obj.article_set.filter(publication_date__gte=start_date)
        article_serializer = ArticleMinimalSerializer(recent_articles, many=True)

        # Get recent warnings
        recent_warnings = obj.warningmessage_set.filter(
            publication_date__gte=start_date
        )
        warning_serializer = WarningMessageMinimalSerializer(recent_warnings, many=True)

        # Combine articles and warnings
        all_items = article_serializer.data + warning_serializer.data
        # Sort combined list by modification_date descending
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
