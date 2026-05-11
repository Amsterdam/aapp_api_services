from django.urls import path

from core.urls import get_swagger_paths
from news.views.base_views import DataLoadView

BASE_PATH = "news/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/extract",
        DataLoadView.as_view(),
        name="data-load-extract",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
