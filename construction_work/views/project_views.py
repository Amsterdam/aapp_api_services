import datetime

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import (
    BooleanField,
    Case,
    DateTimeField,
    F,
    FloatField,
    Max,
    Prefetch,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Greatest, Power, Sqrt
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response

from construction_work.exceptions import (
    MissingArticleIdParam,
    MissingWarningMessageIdParam,
)
from construction_work.models.article_models import Article
from construction_work.models.manage_models import Device, WarningMessage
from construction_work.models.project_models import Project
from construction_work.serializers.article_serializers import ArticleSerializer
from construction_work.serializers.project_serializers import (
    FollowProjectPostDeleteSerializer,
    ProjectExtendedSerializer,
    ProjectExtendedWithFollowersSerializer,
    ProjectFollowedArticlesSerializer,
    WarningMessageWithImagesSerializer,
)
from construction_work.services.geocoding import geocode_address
from construction_work.utils.url_utils import get_media_url
from core.exceptions import MissingDeviceIdHeader
from core.pagination import CustomPagination
from core.utils.openapi_utils import (
    extend_schema_for_api_key,
    extend_schema_for_device_id,
)
from core.views.mixins import DeviceIdMixin


class ProjectListView(DeviceIdMixin, generics.ListAPIView):
    """
    API endpoint that lists active, non-hidden projects.

    Supports filtering by location (lat/lon coordinates or address) and includes
    information about whether the requesting device follows each project.
    Projects can be paginated and include extended project details.

    The projects are ordered based on the following criteria:

    Followed projects are on top:
    - For projects with content: sorted by most recent content date
    - For projects without content:
        - With device location: sorted by shortest distance to project
        - Without device location: sorted by newest project publication date

    Non-followed projects are ordered after the followed projects:
    - With device location: sorted by shortest distance to project
    - Without device location: sorted by newest project publication date

    Required headers:
        - Device-ID: Unique identifier for the requesting device

    Query parameters:
        - lat (str, optional): Latitude coordinate for location filtering
        - lon (str, optional): Longitude coordinate for location filtering
        - address (str, optional): Address string for location filtering (will be geocoded)

    Returns:
        Paginated list of projects with extended details including follow status
    """

    default_date = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    serializer_class = ProjectExtendedSerializer
    pagination_class = CustomPagination

    @extend_schema_for_device_id(
        additional_params=[
            OpenApiParameter("lat", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("lon", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("address", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        success_response=ProjectExtendedSerializer,
        exceptions=[MissingDeviceIdHeader, ParseError],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        device = Device.objects.filter(device_id=self.device_id).first()
        lat, lon = self.get_device_location()

        queryset = Project.objects.filter(active=True, hidden=False)
        queryset = prefetch_recent_articles_and_warnings(queryset)
        queryset = self.annotate_queryset(
            queryset=queryset, device=device, lat=lat, lon=lon
        )
        queryset = self.order_queryset(queryset)
        return queryset

    def get_device_location(self):
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        address = self.request.query_params.get("address")
        if address and (lat is None or lon is None):
            lat, lon = geocode_address(address)
        self.device_location_present = lat is not None and lon is not None
        return lat, lon

    def annotate_queryset(self, *, queryset, device, lat, lon):
        """
        Annotate queryset with main ordering groups
        - 1: followed with content
        - 2: followed without content
        - 3: non-followed (default value)
        """
        queryset = self._annotate_with_latest_content_date(queryset)
        if self.device_location_present:
            queryset = self._annotate_distance(queryset, float(lat), float(lon))

        if device:
            followed_projects = device.followed_projects.filter(
                active=True, hidden=False
            )
            followed_projects_ids = followed_projects.values_list("id", flat=True)
        else:
            followed_projects_ids = []
        queryset = queryset.annotate(
            ordering_group=Case(
                When(id__in=followed_projects_ids, has_content=True, then=Value(1)),
                When(id__in=followed_projects_ids, has_content=False, then=Value(2)),
                default=Value(3),
            )
        )
        # Store context data
        self.followed_projects_ids = list(followed_projects_ids)
        return queryset

    def order_queryset(self, queryset):
        order_fields = ["ordering_group"]
        # Always order by content date for group 1 (followed projects with content)
        order_fields.append(
            Case(
                When(ordering_group=1, then=F("latest_content_date")),
                default=self.default_date,
                output_field=DateTimeField(),
            ).desc()
        )
        if self.device_location_present:
            order_fields.append("distance")
        order_fields.append("-publication_date")
        # Add id as tiebreaker, to avoid duplicates in paginated results
        order_fields.append("id")

        queryset = queryset.order_by(*order_fields)
        return queryset

    def _annotate_with_latest_content_date(self, queryset):
        """
        Annotate queryset with:
        - Latest publication date of related content (articles and warnings)
        - Boolean flag indicating if project has content
        """
        return queryset.annotate(
            latest_article_pub_date=Coalesce(
                Max("article__publication_date"),
                Value(self.default_date, output_field=DateTimeField()),
                output_field=DateTimeField(),
            ),
            latest_warning_pub_date=Coalesce(
                Max("warningmessage__publication_date"),
                Value(self.default_date, output_field=DateTimeField()),
                output_field=DateTimeField(),
            ),
            latest_content_date=Greatest(
                "latest_article_pub_date",
                "latest_warning_pub_date",
                output_field=DateTimeField(),
            ),
            has_content=Case(
                When(latest_content_date__gt=self.default_date, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )

    def _annotate_distance(self, queryset, lat, lon):
        """
        Annotate queryset with distance from given coordinates using Euclidean formula.
        Uses simplified distance calculation that treats Earth as flat plane.

        More accurate calculation is the Haversine formula, but this is more complex
        and requires more computational power.
        With an average of ~11 meters difference between the two calculations,
        within Amsterdam and a maximum of ~46 meters difference,
        this is good enough for our use case.

        The calculation gives a distance in kilometers.
        """
        # Constants for Amsterdam (rough approximation)
        km_per_lat_degree = 111  # km per 1° of latitude
        km_per_lon_degree = 68  # km per 1° of longitude at ~52°N

        # Convert lat/lon degrees to kilometer deltas
        lat_dist = (Cast(F("coordinates_lat"), FloatField()) - lat) * Value(
            km_per_lat_degree, output_field=FloatField()
        )
        lon_dist = (Cast(F("coordinates_lon"), FloatField()) - lon) * Value(
            km_per_lon_degree, output_field=FloatField()
        )

        # distance = sqrt(lat_dist^2 + lon_dist^2)
        distance = Sqrt(Power(lat_dist, 2) + Power(lon_dist, 2))

        return queryset.annotate(distance=distance)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "followed_projects_ids": getattr(self, "followed_projects_ids", []),
            }
        )
        return context


class ProjectSearchView(generics.ListAPIView):
    serializer_class = ProjectExtendedSerializer
    pagination_class = CustomPagination

    @extend_schema_for_api_key(
        additional_params=[
            OpenApiParameter(
                "text", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter("lat", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("lon", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("address", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        success_response=ProjectExtendedSerializer,
        exceptions=[ParseError],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        text = self.request.query_params.get("text")
        if not text or len(text) < settings.MIN_SEARCH_QUERY_LENGTH:
            raise ParseError(
                f"Search text must be at least {settings.MIN_SEARCH_QUERY_LENGTH} characters long."
            )
        similarities = self.get_similarities(text)

        queryset = Project.objects.none()
        if len(similarities) > 1:
            similarity = Greatest(*similarities)
        else:
            similarity = similarities[0]

        if similarity:
            queryset = (
                Project.objects.annotate(similarity=similarity)
                .filter(similarity__gt=0.1, active=True, hidden=False)
                .order_by("-similarity")
            )
        queryset = prefetch_recent_articles_and_warnings(queryset)
        return queryset

    def get_similarities(self, text):
        text_fields = ["title", "subtitle"]
        similarities = []
        for field in text_fields:
            similarity = TrigramSimilarity(field, text)
            if field == "title":
                similarity = similarity * 2
            similarities.append(similarity)

        return similarities

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        address = self.request.query_params.get("address")

        if address and (not lat or not lon):
            lat, lon = geocode_address(address)

        context.update(
            {
                "lat": lat,
                "lon": lon,
                "article_max_age": settings.ARTICLE_MAX_AGE,
            }
        )
        return context


def prefetch_recent_articles_and_warnings(queryset):
    now = timezone.now()
    start_date = now - datetime.timedelta(days=settings.ARTICLE_MAX_AGE)
    recent_articles_prefetch = Prefetch(
        "article_set",
        queryset=Article.objects.filter(publication_date__range=[start_date, now]).only(
            "id", "modification_date"
        ),
        to_attr="recent_articles",
    )
    recent_warnings_prefetch = Prefetch(
        "warningmessage_set",
        queryset=WarningMessage.objects.filter(
            publication_date__range=[start_date, now]
        ).only("id", "modification_date"),
        to_attr="recent_warnings",
    )
    queryset = queryset.prefetch_related(
        recent_articles_prefetch, recent_warnings_prefetch
    )
    return queryset


class ProjectDetailsView(DeviceIdMixin, generics.RetrieveAPIView):
    serializer_class = ProjectExtendedWithFollowersSerializer

    @extend_schema_for_device_id(
        additional_params=[
            OpenApiParameter(
                "id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=True,
                description="Project id",
            ),
        ],
        exceptions=[
            MissingDeviceIdHeader,
            ParseError,
            NotFound,
        ],
        success_response=ProjectExtendedWithFollowersSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
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
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        address = self.request.query_params.get("address")
        if address and (not lat or not lon):
            lat, lon = geocode_address(address)

        device = Device.objects.filter(device_id=self.device_id).first()
        followed_projects_ids = (
            list(device.followed_projects.values_list("pk", flat=True))
            if device
            else []
        )

        context.update(
            {
                "lat": lat,
                "lon": lon,
                "article_max_age": settings.ARTICLE_MAX_AGE,
                "followed_projects_ids": followed_projects_ids,
                "media_url": get_media_url(self.request),
            }
        )
        return context


class FollowProjectView(DeviceIdMixin, generics.GenericAPIView):
    """
    API view to subscribe or unsubscribe from a project.
    """

    @extend_schema_for_device_id(
        request=FollowProjectPostDeleteSerializer,
        exceptions=[MissingDeviceIdHeader, NotFound],
        success_response=str,
        # examples=[OpenApiExample("Example 1", value="Subscription added")],
    )
    def post(self, request, *args, **kwargs):
        """
        Subscribe to a project.
        """
        serializer = FollowProjectPostDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = Project.objects.get(pk=serializer.validated_data["id"])
        except Project.DoesNotExist:
            raise NotFound("Project not found")

        device, _ = Device.objects.get_or_create(device_id=self.device_id)
        device.followed_projects.add(project)
        device.save()

        return Response(data="Subscription added", status=status.HTTP_200_OK)

    @extend_schema_for_device_id(
        exceptions=[MissingDeviceIdHeader, NotFound],
        success_response=str,
        examples=[OpenApiExample("Example 1", value="Subscription removed")],
        description="""
        This endpoint expects a body to be present with a project id defined as 'id'.
        But OpenAPI and therefor DRF spectacular does not support request body for DELETE.
        """,
    )
    def delete(self, request, *args, **kwargs):
        """
        Unsubscribe from a project.
        """
        serializer = FollowProjectPostDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = Project.objects.get(pk=serializer.validated_data["id"])
        except Project.DoesNotExist:
            raise NotFound("Project not found")

        try:
            device = Device.objects.get(device_id=self.device_id)
        except Device.DoesNotExist:
            raise NotFound("Device not found")

        device.followed_projects.remove(project)
        device.save()

        return Response(data="Subscription removed", status=status.HTTP_200_OK)


class FollowedProjectsArticlesView(DeviceIdMixin, generics.GenericAPIView):
    """
    API view to get articles per followed projects
    """

    @extend_schema_for_device_id(
        exceptions=[MissingDeviceIdHeader],
        success_response=ProjectFollowedArticlesSerializer,
        examples=[
            OpenApiExample(
                name="Example 1",
                value={
                    "1": [
                        {
                            "meta_id": {"type": "article", "id": 1},
                            "modification_date": "2023-08-21T11:07:00+02:00",
                        },
                        {
                            "meta_id": {"type": "warning", "id": 2},
                            "modification_date": "2023-08-23T16:28:00+02:00",
                        },
                    ],
                },
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        device = Device.objects.filter(device_id=self.device_id).first()
        if not device:
            # Return empty dictionary if device not found
            return Response(data={}, status=status.HTTP_200_OK)

        followed_projects = device.followed_projects.filter(hidden=False)
        serializer = ProjectFollowedArticlesSerializer(
            followed_projects,
            many=True,
            context={"article_max_age": settings.ARTICLE_MAX_AGE},
        )

        # Transform the list into a dictionary mapping project_id to recent_articles
        result = {
            item["project_id"]: item["recent_articles"] for item in serializer.data
        }

        return Response(data=result, status=status.HTTP_200_OK)


class ArticleDetailView(generics.RetrieveAPIView):
    serializer_class = ArticleSerializer
    queryset = Article.objects.filter(active=True)

    @extend_schema_for_api_key(
        additional_params=[
            OpenApiParameter(
                "id",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Article id",
            ),
        ],
        exceptions=[MissingArticleIdParam, NotFound],
        success_response=ArticleSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        article_id = self.request.query_params.get("id")
        if not article_id:
            raise MissingArticleIdParam
        try:
            article = self.get_queryset().get(pk=article_id)
        except Article.DoesNotExist:
            raise NotFound("Article not found")
        return article


class WarningMessageDetailView(generics.RetrieveAPIView):
    serializer_class = WarningMessageWithImagesSerializer
    queryset = WarningMessage.objects.filter(project__active=True)

    @extend_schema_for_api_key(
        additional_params=[
            OpenApiParameter(
                "id",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Warning id",
            ),
        ],
        exceptions=[MissingWarningMessageIdParam, NotFound],
        success_response=WarningMessageWithImagesSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        message_id = self.request.query_params.get("id", None)
        if not message_id:
            raise MissingWarningMessageIdParam
        try:
            message = self.get_queryset().get(pk=message_id)
        except WarningMessage.DoesNotExist:
            raise NotFound("Warning message not found")
        return message

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "media_url": get_media_url(self.request),
            }
        )
        return context
