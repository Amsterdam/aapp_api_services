from django.urls import include, path

from core.urls import get_swagger_paths

BASE_PATH = "news/api/v1"


_urlpatterns = []

urlpatterns = [
    path(
        BASE_PATH + "/",
        include((_urlpatterns, "news"), namespace="news"),
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
