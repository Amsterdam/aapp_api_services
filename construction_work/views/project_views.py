import datetime
from datetime import timedelta

from django.conf import settings
from django.db.models import Case, DateTimeField, Max, Prefetch, Value, When
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from construction_work.models import Article, Device, Project, WarningMessage
from construction_work.pagination import CustomPagination
from construction_work.serializers import ProjectExtendedSerializer
from construction_work.services.geocoding import geocode_address
from construction_work.utils.geo_utils import calculate_distance


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


class ProjectsListView(generics.RetrieveAPIView):
    serializer_class = ProjectExtendedSerializer
    pagination_class = CustomPagination  # Ensure you have your custom pagination class

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        context = self.get_serializer_context()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True, context=context)
            return Response({"result": serializer.data})

    def get_queryset(self):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise ParseError(
                "Invalid header(s). See /api/v1/apidocs for more information"
            )

        lat = self.request.GET.get("lat")
        lon = self.request.GET.get("lon")
        address = self.request.GET.get("address")

        article_max_age = self.request.GET.get(settings.ARTICLE_MAX_AGE_PARAM, 3)
        try:
            article_max_age = int(article_max_age)
        except ValueError:
            raise ParseError(f"Invalid {settings.ARTICLE_MAX_AGE_PARAM} parameter")

        if address and (lat is None or lon is None):
            lat, lon = geocode_address(address)

        device = Device.objects.filter(device_id=device_id).first()

        # Projects followed by the device
        if device:
            followed_projects_qs = device.followed_projects.filter(
                active=True, hidden=False
            )
            followed_projects_qs = self.annotate_latest_pub_date(followed_projects_qs)
            followed_projects = list(followed_projects_qs.order_by("-latest_pub_date"))
        else:
            followed_projects = []

        # Other projects
        if lat and lon:
            try:
                float(lat)
                float(lon)
            except ValueError:
                raise ParseError("Invalid latitude or longitude")

            other_projects_qs = Project.objects.filter(
                active=True, hidden=False
            ).exclude(pk__in=[p.pk for p in followed_projects])
            other_projects = list(other_projects_qs)
            other_projects.sort(
                key=lambda p: calculate_distance_from_project(p, lat, lon)
            )
        else:
            other_projects_qs = Project.objects.filter(
                active=True, hidden=False
            ).exclude(pk__in=[p.pk for p in followed_projects])
            other_projects_qs = self.annotate_latest_pub_date(other_projects_qs)
            other_projects = list(other_projects_qs.order_by("-latest_pub_date"))

        # Combine followed and other projects
        all_projects = followed_projects + other_projects

        # Prefetch recent articles and warnings
        project_ids = [p.pk for p in all_projects]
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

        if project_ids:
            # Construct preserved_order only if there are projects
            preserved_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(project_ids)]
            )
            queryset = (
                Project.objects.filter(pk__in=project_ids)
                .annotate(ordering=preserved_order)
                .order_by("ordering")
                .prefetch_related(recent_articles_prefetch, recent_warnings_prefetch)
            )
        else:
            # Return an empty queryset
            queryset = Project.objects.none()

        # Store additional context data
        self.lat = lat
        self.lon = lon
        self.followed_projects_ids = [p.pk for p in followed_projects]
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
