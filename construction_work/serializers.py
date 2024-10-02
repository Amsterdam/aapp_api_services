from datetime import timedelta

from django.utils import timezone
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
from construction_work.utils.model_utils import create_id_dict


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
        media_url: str = self.context.get("media_url", "")
        media_url = media_url.rstrip("/")
        if not media_url:
            return None
        return f"{media_url}/{obj.image.name}"


class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer"""

    meta_id = serializers.SerializerMethodField()

    class Meta:
        model = Article
        exclude = ["type"]

    def get_meta_id(self, obj: Article) -> dict:
        return create_id_dict(obj)


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


class ProjectExtendedWithFollowersSerializer(serializers.ModelSerializer):
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

    def get_recent_articles(self, obj: Project) -> list:
        """Get recent articles and warnings"""
        article_max_age = self.context.get("article_max_age", 3)
        media_url = self.context.get("media_url", "")
        start_date = timezone.now() - timedelta(days=article_max_age)

        # Get recent articles
        recent_articles = obj.article_set.filter(
            publication_date__gte=start_date
        ).order_by("-publication_date")
        article_serializer = ArticleSerializer(
            recent_articles, many=True, context={"media_url": media_url}
        )

        # Get recent warnings
        recent_warnings = obj.warningmessage_set.filter(
            publication_date__gte=start_date
        ).order_by("-publication_date")
        warning_serializer = WarningMessageForManagementSerializer(
            recent_warnings, many=True, context={"media_url": media_url}
        )

        # Combine articles and warnings
        all_items = article_serializer.data + warning_serializer.data
        # Sort combined list by modification_date descending
        all_items.sort(key=lambda x: x.get("modification_date", ""), reverse=True)
        return all_items

    def get_meter(self, obj: Project) -> int:
        """Calculate distance from given coordinates to project coordinates"""
        lat = self.context.get("lat")
        lon = self.context.get("lon")
        if not lat or not lon or not obj.coordinates:
            return None

        cords_1 = (float(lat), float(lon))
        project_coordinates = obj.coordinates
        cords_2 = (project_coordinates.get("lat"), project_coordinates.get("lon"))
        if None in cords_2 or (cords_2 == (0, 0)):
            return None
        return calculate_distance(cords_1, cords_2)

    def get_followed(self, obj: Project) -> bool:
        """Check if project is being followed by given device"""
        followed_projects_ids = self.context.get("followed_projects_ids", [])
        return obj.pk in followed_projects_ids

    def get_image(self, obj: Project):
        """Get main image or first image from image list"""
        media_url = self.context.get("media_url", "").rstrip("/")
        if obj.image:
            # If obj.image is a single image instance
            serializer = ImagePublicSerializer(
                obj.image, context={"media_url": media_url}
            )
            return serializer.data
        elif obj.images:
            # If obj.images is a list of images
            first_image = obj.images[0]
            serializer = ImagePublicSerializer(
                first_image, context={"media_url": media_url}
            )
            return serializer.data
        return None
