from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination

from news.models import NewsArticle
from news.serializers.article_serializers import NewsArticleResponseSerializer


class ArticleListView(ListAPIView):
    class DefaultPagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = "page_size"
        max_page_size = 100

    def get_queryset(self):
        return NewsArticle.objects.prefetch_related("images").order_by(
            "-publication_datetime"
        )

    pagination_class = DefaultPagination
    serializer_class = NewsArticleResponseSerializer


class ArticleDetailView(RetrieveAPIView):
    def get_queryset(self):
        return NewsArticle.objects.prefetch_related("images")

    serializer_class = NewsArticleResponseSerializer
    lookup_field = "id"
