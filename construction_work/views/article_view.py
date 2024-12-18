from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from construction_work.models.article_models import Article
from construction_work.models.manage_models import WarningMessage
from construction_work.serializers.article_serializers import (
    ArticleListSerializer,
    WarningMessageListSerializer,
)
from construction_work.utils.url_utils import get_media_url
from core.views.extend_schema import extend_schema_for_api_key as extend_schema


class ArticleListView(generics.GenericAPIView):
    """
    API view to get articles and warnings, optionally filtered by project IDs.
    """

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                "project_ids",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Project ids, comma seperated",
            ),
            OpenApiParameter("sort_by", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("sort_order", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("limit", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        exceptions=[ParseError],
        success_response=ArticleListSerializer,
    )
    def get(self, request, *args, **kwargs):
        # Handle 'project_ids' parameter
        project_ids_param = request.query_params.get("project_ids")
        project_ids = []
        if project_ids_param:
            project_ids = project_ids_param.split(",")
            if not all(pid.isdigit() for pid in project_ids):
                raise ParseError(
                    "Invalid 'project_ids' parameter. IDs must be integers."
                )
            project_ids = [int(pid) for pid in project_ids]

        # Handle 'sort_by' and 'sort_order' parameters
        sort_by = request.query_params.get("sort_by", "publication_date")
        sort_order = request.query_params.get("sort_order", "desc")
        if sort_order not in ["asc", "desc"]:
            raise ParseError("Invalid 'sort_order' parameter. Must be 'asc' or 'desc'.")

        # Handle 'limit' parameter
        limit_param = request.query_params.get("limit", "0")
        if not limit_param.isdigit():
            raise ParseError(
                "Invalid 'limit' parameter. Must be a non-negative integer."
            )
        limit = int(limit_param)
        if limit < 0:
            raise ParseError("'limit' parameter must be non-negative.")

        # # Collect articles
        # articles_qs = Article.objects.filter(active=True).prefetch_related("image")
        # if project_ids:
        #     articles_qs = articles_qs.filter(projects__id__in=project_ids)
        # articles_qs = articles_qs.only("id", "title", "publication_date", "image")
        #
        # # Collect warnings
        # warnings_qs = (
        #     WarningMessage.objects.filter(project__active=True)
        #     .select_related("project")
        #     .prefetch_related("warningimage_set", "warningimage_set__images")
        # )
        # if project_ids:
        #     warnings_qs = warnings_qs.filter(project__id__in=project_ids)

        # Collect articles
        articles_qs = Article.objects.filter(active=True)
        if project_ids:
            articles_qs = articles_qs.filter(projects__id__in=project_ids)
        articles_qs = articles_qs.only("id", "title", "publication_date", "image")

        # Collect warnings
        warnings_qs = WarningMessage.objects.filter(project__active=True)
        if project_ids:
            warnings_qs = warnings_qs.filter(project__id__in=project_ids)
        warnings_qs = warnings_qs.prefetch_related("warningimage_set__images")

        # Serialize articles and warnings
        articles_serializer = ArticleListSerializer(articles_qs, many=True)
        warnings_serializer = WarningMessageListSerializer(
            warnings_qs, many=True, context={"media_url": get_media_url(request)}
        )

        # Combine articles and warnings
        all_news = articles_serializer.data + warnings_serializer.data

        # Determine available sort keys dynamically
        available_sort_keys = []
        if all_news:
            # Collect keys from all items to handle cases where items have different keys
            all_keys = set()
            for item in all_news:
                all_keys.update(item.keys())
            available_sort_keys = list(all_keys)

        if available_sort_keys and sort_by not in available_sort_keys:
            raise ParseError(
                f"Invalid 'sort_by' parameter. Available options are {available_sort_keys}."
            )

        # Sort combined list
        try:
            all_news.sort(
                key=lambda x: x.get(sort_by, ""), reverse=sort_order == "desc"
            )
        except TypeError as e:
            raise ParseError(f"Unable to sort by '{sort_by}': {str(e)}")

        # Apply limit if specified
        if limit > 0:
            all_news = all_news[:limit]

        return Response(all_news, status=status.HTTP_200_OK)
