from django.urls import path

from core.urls import get_admin_paths, get_swagger_paths
from modules.views import AppReleaseListView, ReleaseDetailView

BASE_PATH = "modules/api/v1"
BASE_PATH_ADMIN = "modules/admin"

urlpatterns = [
    path(
        BASE_PATH + "/release/<str:version>",
        ReleaseDetailView.as_view(),
        name="modules-release-detail",
    ),
    path(
        BASE_PATH + "/releases",
        AppReleaseListView.as_view(),
        name="modules-release-list",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
urlpatterns += get_admin_paths(BASE_PATH_ADMIN, enable_oidc=False)
