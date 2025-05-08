from django.urls import path

from core.urls import get_swagger_paths
from image import views

BASE_PATH = "image/api/v1"
BASE_PATH_INTERNAL = "internal/api/v1"


urlpatterns = [
    path(
        BASE_PATH_INTERNAL + "/image",
        views.ImageSetCreateView.as_view(),
        name="image-create-imageset",
    ),
    path(
        BASE_PATH_INTERNAL + "/image/from_url",
        views.ImageSetFromUrlCreateView.as_view(),
        name="image-create-imageset-from-url",
    ),
    path(
        BASE_PATH_INTERNAL + "/image/<int:pk>",
        views.ImageSetDetailView.as_view(),
        name="image-detail-imageset",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
