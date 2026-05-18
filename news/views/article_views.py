import logging

from rest_framework.generics import ListAPIView

from news.models import NewsArticle
from news.serializers.article_serializers import NewsArticleListResponseSerializer

logger = logging.getLogger(__name__)


class ArticleListView(ListAPIView):
    def get_queryset(self):
        return NewsArticle.objects.prefetch_related("images").order_by(
            "-publication_date"
        )

    serializer_class = NewsArticleListResponseSerializer
