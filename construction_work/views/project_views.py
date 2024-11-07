import datetime
from datetime import timedelta

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
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
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response

from construction_work.exceptions import (
    InvalidArticleMaxAgeParam,
    MissingArticleIdParam,
    MissingDeviceIdHeader,
    MissingWarningMessageIdParam,
)
from construction_work.models import Article, Device, Project, WarningMessage
from construction_work.pagination import CustomPagination
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
from core.views.extend_schema import extend_schema_for_api_key as extend_schema


class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectExtendedSerializer
    pagination_class = CustomPagination

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            ),
            OpenApiParameter("lat", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("lon", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("address", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        success_response=ProjectExtendedSerializer,
        exceptions=[MissingDeviceIdHeader, InvalidArticleMaxAgeParam, ParseError],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        address = self.request.query_params.get("address")

        article_max_age = self.request.query_params.get(
            settings.ARTICLE_MAX_AGE_PARAM, 3
        )
        try:
            article_max_age = int(article_max_age)
        except ValueError:
            raise InvalidArticleMaxAgeParam

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
                "lat": getattr(self, "lat", None),
                "lon": getattr(self, "lon", None),
                "followed_projects_ids": getattr(self, "followed_projects_ids", []),
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


class ProjectSearchView(generics.ListAPIView):
    serializer_class = ProjectExtendedSerializer
    pagination_class = CustomPagination

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                "text", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                "query_fields", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                "fields", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter("lat", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("lon", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("address", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        success_response=ProjectExtendedSerializer,
        exceptions=[InvalidArticleMaxAgeParam, ParseError],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        text = self.request.query_params.get("text")
        query_fields = self.request.query_params.get("query_fields")
        return_fields = self.request.query_params.get("fields")

        if not text or len(text) < settings.MIN_SEARCH_QUERY_LENGTH:
            raise ParseError(
                f"Search text must be at least {settings.MIN_SEARCH_QUERY_LENGTH} characters long."
            )

        if not query_fields:
            raise ParseError("Query fields are required.")

        # Validate query fields
        model_fields = [
            field.name for field in Project._meta.get_fields() if not field.is_relation
        ]
        query_fields_list = query_fields.split(",")
        for field in query_fields_list:
            if field not in model_fields:
                raise ParseError(
                    f"Field '{field}' is not a valid field in Project model."
                )

        # Validate return fields if provided
        return_fields_list = None
        if return_fields:
            return_fields_list = return_fields.split(",")
            for field in return_fields_list:
                if field not in model_fields:
                    raise ParseError(
                        f"Field '{field}' is not a valid field in Project model."
                    )

        similarities = [TrigramSimilarity(field, text) for field in query_fields_list]

        # Start off with empty queryset
        queryset = Project.objects.none()

        similarity = similarities[0]
        if len(similarities) > 1:
            similarity = Greatest(*similarities)

        if similarity:
            queryset = (
                Project.objects.annotate(similarity=similarity)
                .filter(similarity__gt=0.1, active=True, hidden=False)
                .order_by("-similarity")
            )

        # Optimize the queryset to only include necessary fields
        if return_fields_list:
            queryset = queryset.only(*return_fields_list)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        address = self.request.query_params.get("address")

        if address and (not lat or not lon):
            lat, lon = geocode_address(address)

        article_max_age = self.request.query_params.get(
            settings.ARTICLE_MAX_AGE_PARAM, 3
        )
        try:
            article_max_age = int(article_max_age)
        except ValueError:
            raise InvalidArticleMaxAgeParam

        context.update(
            {
                "lat": lat,
                "lon": lon,
                "article_max_age": article_max_age,
            }
        )
        return context

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return_fields = self.request.query_params.get("fields")
        if return_fields:
            fields = return_fields.split(",")
            kwargs["fields"] = fields
        return serializer_class(*args, **kwargs)


class ProjectDetailsView(generics.RetrieveAPIView):
    serializer_class = ProjectExtendedWithFollowersSerializer

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            ),
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
            InvalidArticleMaxAgeParam,
        ],
        success_response=ProjectExtendedWithFollowersSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        device_id = self.request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

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
            raise InvalidArticleMaxAgeParam

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


class FollowProjectView(generics.GenericAPIView):
    """
    API view to subscribe or unsubscribe from a project.
    """

    @extend_schema(
        request=FollowProjectPostDeleteSerializer,
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            ),
        ],
        exceptions=[MissingDeviceIdHeader, NotFound],
        success_response=str,
        examples=[OpenApiExample("Example 1", value="Subscription added")],
    )
    def post(self, request, *args, **kwargs):
        """
        Subscribe to a project.
        """
        device_id = request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        serializer = FollowProjectPostDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = Project.objects.get(pk=serializer.validated_data["id"])
        except Project.DoesNotExist:
            raise NotFound("Project not found")

        device, _ = Device.objects.get_or_create(device_id=device_id)
        device.followed_projects.add(project)
        device.save()

        return Response(data="Subscription added", status=status.HTTP_200_OK)

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            ),
        ],
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
        device_id = request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        serializer = FollowProjectPostDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = Project.objects.get(pk=serializer.validated_data["id"])
        except Project.DoesNotExist:
            raise NotFound("Project not found")

        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            raise NotFound("Device not found")

        device.followed_projects.remove(project)
        device.save()

        return Response(data="Subscription removed", status=status.HTTP_200_OK)


class FollowedProjectsArticlesView(generics.GenericAPIView):
    """
    API view to get articles per followed projects
    """

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            ),
            OpenApiParameter(
                settings.ARTICLE_MAX_AGE_PARAM, OpenApiTypes.STR, OpenApiParameter.QUERY
            ),
        ],
        exceptions=[MissingDeviceIdHeader, InvalidArticleMaxAgeParam],
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
        device_id = request.headers.get(settings.HEADER_DEVICE_ID)
        if not device_id:
            raise MissingDeviceIdHeader

        device = Device.objects.filter(device_id=device_id).first()
        if not device:
            # Return empty dictionary if device not found
            return Response(data={}, status=status.HTTP_200_OK)

        article_max_age = request.query_params.get(
            settings.ARTICLE_MAX_AGE_PARAM, settings.DEFAULT_ARTICLE_MAX_AGE
        )
        try:
            article_max_age = int(article_max_age)
        except ValueError:
            raise InvalidArticleMaxAgeParam

        followed_projects = device.followed_projects.filter(hidden=False)

        serializer = ProjectFollowedArticlesSerializer(
            followed_projects, many=True, context={"article_max_age": article_max_age}
        )

        # Transform the list into a dictionary mapping project_id to recent_articles
        result = {
            item["project_id"]: item["recent_articles"] for item in serializer.data
        }

        return Response(data=result, status=status.HTTP_200_OK)


class ArticleDetailView(generics.RetrieveAPIView):
    serializer_class = ArticleSerializer
    queryset = Article.objects.filter(active=True)

    @extend_schema(
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

    @extend_schema(
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
