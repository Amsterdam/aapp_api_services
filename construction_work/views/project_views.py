import datetime
from datetime import timedelta

from django.conf import settings
from django.db.models import (
    BooleanField,
    DateTimeField,
    Exists,
    F,
    FloatField,
    Max,
    OuterRef,
    Prefetch,
    Value,
)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, Coalesce, Greatest
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response

from construction_work.models import Article, Device, Project, WarningMessage
from construction_work.pagination import CustomPagination
from construction_work.serializers import (
    ProjectExtendedSerializer,
    ProjectExtendedWithFollowersSerializer,
)
from construction_work.services.geocoding import geocode_address
from construction_work.utils.geo_utils import calculate_distance
from construction_work.utils.url_utils import get_media_url


def calculate_distance_from_project(project: Project, lat, lon):
    """Calculate the distance between given coordinates and project coordinates."""
    given_coords = (float(lat), float(lon))

    if project.coordinates is not None:
        project_coords = (
            project.coordinates.get("lat"),
            project.coordinates.get("lon"),
        )
    else:
        project_coords = (None, None)

    meter = calculate_distance(given_coords, project_coords)
    return meter if meter is not None else float("inf")


class ProjectListView(generics.RetrieveAPIView):
    serializer_class = ProjectExtendedSerializer
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        context = self.get_serializer_context()

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise ParseError(f"Missing header: {settings.HEADER_DEVICE_ID}")

        lat = self.request.GET.get("lat")
        lon = self.request.GET.get("lon")
        address = self.request.GET.get("address")

        article_max_age = self.request.GET.get(settings.ARTICLE_MAX_AGE_PARAM, 3)
        try:
            article_max_age = int(article_max_age)
        except ValueError:
            raise ParseError(f"Invalid parameter: {settings.ARTICLE_MAX_AGE_PARAM}")

        if address and (lat is None or lon is None):
            lat, lon = geocode_address(address)

        device = Device.objects.filter(device_id=device_id).first()

        # Start with all active, non-hidden projects
        projects_qs = Project.objects.filter(active=True, hidden=False)

        # Annotate projects with whether they are followed by the device
        if device:
            # Use Exists subquery to annotate is_followed
            followed_projects = device.followed_projects.filter(
                active=True, hidden=False
            )
            projects_qs = projects_qs.annotate(
                is_followed=Exists(followed_projects.filter(pk=OuterRef("pk")))
            )
            self.followed_projects_ids = list(
                followed_projects.values_list("pk", flat=True)
            )
        else:
            # Annotate all projects as not followed
            projects_qs = projects_qs.annotate(
                is_followed=Value(False, output_field=BooleanField())
            )
            self.followed_projects_ids = []

        # Annotate and order projects based on provided latitude and longitude
        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                raise ParseError(f"Invalid latitude or longitude: {lat=}, {lon=}")

            # Extract latitude and longitude from JSONField 'coordinates'
            projects_qs = projects_qs.annotate(
                coord_lat=Cast(KeyTextTransform("lat", "coordinates"), FloatField()),
                coord_lon=Cast(KeyTextTransform("lon", "coordinates"), FloatField()),
            )

            # Calculate approximate distance (squared difference)
            # The calculated distance is not perfect,
            # since this method treats the Earth as a flat plane.
            # But this form of calculation is far less expensive.
            # When sorting, the order of distances remains the same,
            # whether you use the squared distance or the actual distance.
            projects_qs = projects_qs.annotate(
                lat_diff=F("coord_lat") - lat,
                lon_diff=F("coord_lon") - lon,
            ).annotate(
                distance=F("lat_diff") * F("lat_diff") + F("lon_diff") * F("lon_diff")
            )

            # Order projects by is_followed and distance
            projects_qs = projects_qs.order_by("-is_followed", "distance")
        else:
            # Annotate projects with latest publication date
            projects_qs = self.annotate_latest_pub_date(projects_qs)
            # Order projects by is_followed and latest_pub_date
            projects_qs = projects_qs.order_by("-is_followed", "-latest_pub_date")

        # Prefetch recent articles and warnings
        now = timezone.now()
        start_date = now - timedelta(days=article_max_age)

        recent_articles_prefetch = Prefetch(
            "article_set",
            queryset=Article.objects.filter(
                publication_date__range=[start_date, now]
            ).only("id", "modification_date"),
            to_attr="recent_articles",
        )

        recent_warnings_prefetch = Prefetch(
            "warningmessage_set",
            queryset=WarningMessage.objects.filter(
                publication_date__range=[start_date, now]
            ).only("id", "modification_date"),
            to_attr="recent_warnings",
        )

        queryset = projects_qs.prefetch_related(
            recent_articles_prefetch, recent_warnings_prefetch
        )

        # Store additional context data
        self.lat = lat
        self.lon = lon

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "lat": self.lat,
                "lon": self.lon,
                "followed_projects_ids": self.followed_projects_ids,
            }
        )
        return context

    def annotate_latest_pub_date(self, queryset):
        """Annotate queryset with the latest publication date of articles and warnings."""
        default_date = datetime.datetime(1970, 1, 1, tzinfo=timezone.utc)
        return queryset.annotate(
            latest_article_pub_date=Coalesce(
                Max("article__publication_date"),
                Value(default_date, output_field=DateTimeField()),
                output_field=DateTimeField(),
            ),
            latest_warning_pub_date=Coalesce(
                Max("warningmessage__publication_date"),
                Value(default_date, output_field=DateTimeField()),
                output_field=DateTimeField(),
            ),
            latest_pub_date=Greatest(
                "latest_article_pub_date",
                "latest_warning_pub_date",
                output_field=DateTimeField(),
            ),
        )


class ProjectDetailsView(generics.RetrieveAPIView):
    serializer_class = ProjectExtendedWithFollowersSerializer

    def get_queryset(self):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise ParseError(f"Missing header: {settings.HEADER_DEVICE_ID}")

        project_id = self.request.query_params.get("id")
        if not project_id:
            raise ParseError("Missing project id")

        queryset = Project.objects.filter(pk=project_id, active=True)
        if not queryset.exists():
            raise NotFound("No record found")

        return queryset

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()

        article_max_age = self.request.query_params.get(
            settings.ARTICLE_MAX_AGE_PARAM, settings.DEFAULT_ARTICLE_MAX_AGE
        )
        try:
            article_max_age = int(article_max_age)
        except ValueError:
            raise ParseError(f"Invalid parameter: {settings.ARTICLE_MAX_AGE_PARAM}")

        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        address = self.request.query_params.get("address")
        if address and (not lat or not lon):
            lat, lon = geocode_address(address)

        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        device = Device.objects.filter(device_id=device_id).first()
        followed_projects_ids = (
            list(device.followed_projects.values_list("pk", flat=True))
            if device
            else []
        )

        context.update(
            {
                "lat": lat,
                "lon": lon,
                "article_max_age": article_max_age,
                "followed_projects_ids": followed_projects_ids,
                "media_url": get_media_url(self.request),
            }
        )
        return context
