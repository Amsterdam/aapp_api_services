from django.urls import path

from core.urls import get_swagger_paths
from news.views import article_views

BASE_PATH = "news/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/articles",
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
