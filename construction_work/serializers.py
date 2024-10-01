from rest_framework import serializers

from construction_work.models import Project


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
        from construction_work.views.project_views import get_distance

        """Give distrance away from project in meters"""
        lat = self.context.get("lat")
        lon = self.context.get("lon")
        if obj is None:
            return None

        cords_1 = lat, lon
        project_coordinates = obj.coordinates
        if project_coordinates is None:
            project_coordinates = {"lat": None, "lon": None}
        cords_2 = (project_coordinates.get("lat"), project_coordinates.get("lon"))
        if None in cords_2:
            cords_2 = (None, None)
        elif (0, 0) == cords_2:
            cords_2 = (None, None)
        meter = get_distance(cords_1, cords_2)
        return meter

    def get_followed(self, obj: Project) -> bool:
        """Check if project is being followed by given device"""
        followed_projects = self.context.get("followed_projects")
        if followed_projects is None:
            return None

        return obj.pk in [x.pk for x in followed_projects]

    def get_recent_articles(self, obj: Project) -> dict:
        """Get recent articles"""
        project_news_mapping = self.context.get("project_news_mapping")
        if project_news_mapping is None:
            return []

        return project_news_mapping[obj.pk]

    def get_image(self, obj: Project):
        """Get main image or first image from image list"""
        if obj.image:
            return obj.image
        if obj.images:
            return obj.images[0]
        return {}
