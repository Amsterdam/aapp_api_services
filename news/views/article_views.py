import logging

from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.utils.openapi_utils import extend_schema_for_api_key
from news.models import NewsArticle
from news.serializers.article_serializers import (
    NewsArticleRequestSerializer,
    NewsArticleResponseSerializer,
)

logger = logging.getLogger(__name__)


class ArticleListView(ListAPIView):
    serializer_class = NewsArticleResponseSerializer

    def get_queryset(self):
        query_serializer = NewsArticleRequestSerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)

        article_type = query_serializer.validated_data["type"]
        queryset = (
            NewsArticle.objects.filter(type=article_type)
            .prefetch_related("images")
            .order_by("-publication_date")
        )

        if article_type == "district":
            district = query_serializer.validated_data.get("district")
            queryset = queryset.filter(district=district)
        return queryset

    @extend_schema_for_api_key(
        additional_params=[NewsArticleRequestSerializer],
        success_response=NewsArticleResponseSerializer(many=True),
    )
    def get(self):
        return super().get(self.request)


class ArticleDetailView(RetrieveAPIView):
    def get_queryset(self):
        return NewsArticle.objects.prefetch_related("images")

    serializer_class = NewsArticleResponseSerializer
    lookup_field = "id"
