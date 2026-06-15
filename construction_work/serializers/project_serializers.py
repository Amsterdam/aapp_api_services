from datetime import timedelta
from typing import Optional

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from construction_work.models.article_models import Article
from construction_work.models.manage_models import ProjectManager, WarningMessage
from construction_work.models.project_models import (
    Project,
    ProjectContact,
    ProjectImage,
    ProjectImageSource,
    ProjectTimelineItem,
)
from construction_work.serializers.article_serializers import (
    ArticleSerializer,
)
from construction_work.serializers.general_serializers import (
    DynamicFieldsModelSerializer,
    ImagePublicSerializer,
    IproxCoordinatesSerializer,
    IproxImageSerializer,
    IproxProjectSectionsSerializer,
    IproxProjectTimelineSerializer,
    MetaIdSerializer,
)
from construction_work.utils.model_utils import create_id_dict


class ProjectImageSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImageSource
        exclude = ["image", "id"]


class ProjectImageSerializer(serializers.ModelSerializer):
    sources = ProjectImageSourceSerializer(many=True)

    class Meta:
        model = ProjectImage
        exclude = ["parent"]


class RecentArticlesIdDateSerializer(serializers.Serializer):
    meta_id = MetaIdSerializer()
    modification_date = serializers.DateTimeField()


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

    def get_meter(self, obj: Project) -> Optional[int]:
        """
        Convert kilometers to meters.
        """
        if not hasattr(obj, "distance"):
            return None
        if obj.distance is None:
            return None

        # Convert kilometers to meters
        return int(obj.distance * 1000)

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


class ProjectManagerNameEmailSerializer(serializers.ModelSerializer):
    """Project manager serializer"""

    class Meta:
        model = ProjectManager
        fields = ["name", "email"]


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
            if not warning_image.image_set.exists():
                continue

            image_serializer = ImagePublicSerializer(
                warning_image.image_set.all(),
                many=True,
                context={"media_url": media_url},
            )
            sources = image_serializer.data

            first_image = warning_image.image_set.first()
            image = {
                "id": warning_image.image_set_id,
                "sources": sources,
                "landscape": bool(first_image.width > first_image.height),
                "alternativeText": first_image.description,
            }
            images.append(image)
        return images


class WarningMessageSerializer(WarningMessageWithImagesSerializer):
    """Warning message serializer for management interface"""

    publisher = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        exclude = ["project_manager", "author_email"]

    @extend_schema_field(ProjectManagerNameEmailSerializer)
    def get_publisher(self, obj: WarningMessage):
        serializer = ProjectManagerNameEmailSerializer(obj.project_manager)
        return serializer.data


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
        warning_serializer = WarningMessageSerializer(
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
        collapsed_idx = [
            i for i, item in enumerate(timeline_items) if not item.collapsed
        ]
        if not collapsed_idx:
            first, last = 0, len(timeline_items) - 1
        else:
            first, last = collapsed_idx[0], collapsed_idx[-1]

        response = []
        for i, item in enumerate(timeline_items):
            items = self.get_timeline_items(item.items.all())
            if i < first:
                progress = "done"
            elif first <= i <= last:
                progress = "active"
            else:
                progress = "planned"
            response.append(
                {
                    "title": item.title,
                    "body": item.body,
                    "collapsed": item.collapsed,
                    "progress": progress,
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


class WarningMessageMinimalSerializer(serializers.ModelSerializer):
    """Waring message serializer with meta id field"""

    meta_id = serializers.SerializerMethodField()

    class Meta:
        model = WarningMessage
        fields = ["meta_id", "modification_date"]

    @extend_schema_field(MetaIdSerializer)
    def get_meta_id(self, obj: WarningMessage) -> dict:
        return obj.get_id_dict()


class ArticleMinimalSerializer(ArticleSerializer):
    """Article serializer with minimal data"""

    class Meta:
        model = Article
        fields = ["meta_id", "modification_date"]


class FollowProjectPostDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
