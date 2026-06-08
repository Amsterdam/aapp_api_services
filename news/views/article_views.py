from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.pagination import CustomPagination
from core.utils.openapi_utils import extend_schema_for_api_key
from news.models import NewsArticle
from news.serializers.article_serializers import (
    NewsArticleDetailResponseSerializer,
    NewsArticleListResponseSerializer,
    NewsArticleRequestSerializer,
)

ARTICLE_LIST_CACHE_TTL_SECONDS = 60 * 5
ARTICLE_DETAIL_CACHE_TTL_SECONDS = 60


@method_decorator(cache_page(ARTICLE_LIST_CACHE_TTL_SECONDS), name="get")
class ArticleListView(ListAPIView):
    pagination_class = CustomPagination
    serializer_class = NewsArticleListResponseSerializer

    def get_queryset(self):
        query_serializer = NewsArticleRequestSerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)

        article_type = query_serializer.validated_data["type"]
        queryset = (
            NewsArticle.visible_objects.filter(type=article_type)
            .prefetch_related("images")
            .order_by("-publication_datetime")
        )

        if article_type == "district":
            district = query_serializer.validated_data.get("district")
            queryset = queryset.filter(district=district)
        return queryset

    @extend_schema_for_api_key(
        additional_params=[NewsArticleRequestSerializer],
        success_response=NewsArticleListResponseSerializer(many=True),
    )
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


@method_decorator(cache_page(ARTICLE_DETAIL_CACHE_TTL_SECONDS), name="get")
class ArticleDetailView(RetrieveAPIView):
    def get_queryset(self):
        return NewsArticle.visible_objects.prefetch_related(
            "images", "liveblog_items__images"
        )

    serializer_class = NewsArticleDetailResponseSerializer
    lookup_field = "id"

    @extend_schema_for_api_key(
        success_response=NewsArticleDetailResponseSerializer,
    )
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)
