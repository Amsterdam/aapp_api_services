from rest_framework.generics import ListAPIView, RetrieveAPIView

from news.models import NewsArticle
from news.serializers.article_serializers import NewsArticleResponseSerializer


class ArticleListView(ListAPIView):
    def get_queryset(self):
        return NewsArticle.objects.prefetch_related("images").order_by(
            "-publication_date"
        )

    serializer_class = NewsArticleResponseSerializer


class ArticleDetailView(RetrieveAPIView):
    def get_queryset(self):
        return NewsArticle.objects.prefetch_related("images")

    serializer_class = NewsArticleResponseSerializer
    lookup_field = "id"
