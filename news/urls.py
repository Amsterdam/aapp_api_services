from django.urls import path, register_converter

from core.urls import get_swagger_paths
from news.models import ARTICLE_TYPE_CHOICES
from news.views import article_views

BASE_PATH = "news/api/v1"

class ArticleTypeConverter:
    regex = "|".join(choice[0] for choice in ARTICLE_TYPE_CHOICES)

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(ArticleTypeConverter, "article_type")

urlpatterns = [
    path(
        BASE_PATH + "/articles/<article_type:type>",
        article_views.ArticleListView.as_view(),
        name="news-article-list",
    ),
    path(
        BASE_PATH + "/articles/<int:id>/",
        article_views.ArticleDetailView.as_view(),
        name="news-article-detail",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
