from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.pagination import CustomPagination
from core.utils.openapi_utils import extend_schema_for_api_key
from news.models import NewsArticle
from news.serializers.article_serializers import (
    NewsArticleDetailResponseSerializer,
    NewsArticleListResponseSerializer,
    NewsArticleRequestSerializer,
)


class ArticleListView(ListAPIView):
    pagination_class = CustomPagination
    serializer_class = NewsArticleListResponseSerializer

    def get_queryset(self):
        query_serializer = NewsArticleRequestSerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)

        article_type = query_serializer.validated_data["type"]
        queryset = (
            NewsArticle.objects.filter(type=article_type)
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


class ArticleDetailView(RetrieveAPIView):
    def get_queryset(self):
        return NewsArticle.objects.prefetch_related("images", "liveblog_items__images")

    serializer_class = NewsArticleDetailResponseSerializer
    lookup_field = "id"

    @extend_schema_for_api_key(
        success_response=NewsArticleDetailResponseSerializer,
    )
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)
