import logging

from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from news.models import NewsArticle
from news.serializers.article_serializers import NewsArticleListResponseSerializer

logger = logging.getLogger(__name__)


class ArticleListView(ListAPIView):
    class DefaultPagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = "page_size"
        max_page_size = 100

    queryset = NewsArticle.objects.prefetch_related("images").order_by(
        "-publication_datetime"
    )
    pagination_class = DefaultPagination
    serializer_class = NewsArticleListResponseSerializer
