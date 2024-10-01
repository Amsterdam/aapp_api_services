from rest_framework import serializers

from construction_work.models import Project
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
