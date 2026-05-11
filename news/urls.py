from django.urls import path

from core.urls import get_swagger_paths
from news.views import base_views

BASE_PATH = "news/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/data-extract",
        base_views.DataLoadView.as_view(),
        name="news-data-extract",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
