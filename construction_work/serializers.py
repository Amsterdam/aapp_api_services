from rest_framework import serializers

from construction_work.models import (
    Article,
    Image,
    Notification,
    Project,
    ProjectManager,
    WarningMessage,
)
from construction_work.utils.geo_utils import calculate_distance
from construction_work.utils.model_utils import (
    create_id_dict,
    get_recent_articles_and_warnings_of_project,
)


class ProjectExtendedSerializer(serializers.ModelSerializer):
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
        followed_projects_ids = self.context.get("followed_projects_ids")
        if followed_projects_ids is None:
            return False

        return obj.pk in followed_projects_ids

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

    def get_image(self, obj: Project):
        """Get main image or first image from image list"""
        if obj.image:
            return obj.image
        if obj.images:
            return obj.images[0]
        return {}


class ProjectManagerNameEmailSerializer(serializers.ModelSerializer):
    """Project manager serializer"""

    class Meta:
        model = ProjectManager
        fields = ["name", "email"]


class ImagePublicSerializer(serializers.ModelSerializer):
    """Image public serializer"""

    uri = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["uri", "width", "height"]

    def get_uri(self, obj: Image):
        """Get URI"""
        media_url: str = self.context.get("media_url")
        media_url = media_url.rstrip("/")
        if media_url is None:
            return None
        return f"{media_url}/{obj.image.name}"


class ProjectExtendedWithFollowersSerializer(ProjectExtendedSerializer):
    """Project details serializer"""

    followers = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ["hidden"]

    def get_field_names(self, *args, **kwargs):
        """Get field names"""
        field_names = self.context.get("fields", None)
        if field_names:
            return field_names
        return super().get_field_names(*args, **kwargs)

    def get_followers(self, obj: Project) -> int:
        """Get amount of followers of project"""
        return obj.device_set.count()

    def get_recent_articles(self, obj: Project) -> list:
        """Get recent articles"""
        article_max_age = self.context.get("article_max_age")
        media_url = self.context.get("media_url")
        return get_recent_articles_and_warnings_of_project(
            obj,
            article_max_age,
            ArticleSerializer,
            WarningMessageForManagementSerializer,
            context={
                "media_url": media_url,
            },
        )


class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer"""

    meta_id = serializers.SerializerMethodField()

    class Meta:
        model = Article
        exclude = ["type"]

    def get_meta_id(self, obj: Article) -> dict:
        return obj.get_id_dict()


class WarningMessageMetaIdSerializer(serializers.ModelSerializer):
    """Waring message serializer with meta id field"""

    meta_id = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        fields = "__all__"

    def get_meta_id(self, obj: WarningMessage) -> dict:
        return obj.get_id_dict()


class WarningMessageWithImagesSerializer(WarningMessageMetaIdSerializer):
    """Warning message with images serializer"""

    images = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager"]

    def get_images(self, obj: WarningMessage):
        """Get images"""
        media_url = self.context.get("media_url")
        warning_images = obj.warningimage_set.all()

        images = []
        for warning_image in warning_images:
            image_serializer = ImagePublicSerializer(
                instance=warning_image.images.all(),
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
        if Notification.objects.filter(warning=obj).exists():
            return True
        return False


class WarningMessageWithImagesSerializer(WarningMessageMetaIdSerializer):
    """Warning message with images serializer"""

    images = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager"]

    def get_images(self, obj: WarningMessage):
        """Get images"""
        media_url = self.context.get("media_url")
        warning_images = obj.warningimage_set.all()

        images = []
        for warning_image in warning_images:
            image_serializer = ImagePublicSerializer(
                instance=warning_image.images.all(),
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
