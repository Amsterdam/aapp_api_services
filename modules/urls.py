from django.urls import path

from core.urls import get_swagger_paths
from modules.views.module_version_views import (
    ModuleVersionCreateView,
    ModuleVersionDetailView,
    ModuleVersionStatusView,
)
from modules.views.module_views import ModuleCreateView, ModuleDetailView
from modules.views.modules_views import (
    ModulesAvailableForReleaseView,
    ModulesLatestView,
)
from modules.views.release_views import ReleaseCreateView, ReleaseDetailView
from modules.views.releases_views import GetReleasesView

BASE_PATH = "modules/api/v1"

urlpatterns = [
    # module version
    path(
        BASE_PATH + "/module/<str:slug>/version/<str:version>/status",
        ModuleVersionStatusView.as_view(),
    ),
    path(
        BASE_PATH + "/module/<str:slug>/version/<str:version>",
        ModuleVersionDetailView.as_view(),
    ),
    # module
    path(
        BASE_PATH + "/module/<str:slug>/version",
        ModuleVersionCreateView.as_view(),
    ),
    path(
        BASE_PATH + "/module",
        ModuleCreateView.as_view(),
    ),
    path(
        BASE_PATH + "/module/<str:slug>",
        ModuleDetailView.as_view(),
    ),
    # modules
    path(
        BASE_PATH + "/modules/latest",
        ModulesLatestView.as_view(),
    ),
    path(
        BASE_PATH + "/modules/available-for-release/<str:release_version>",
        ModulesAvailableForReleaseView.as_view(),
    ),
    # release
    path(
        BASE_PATH + "/release",
        ReleaseCreateView.as_view(),
    ),
    path(
        BASE_PATH + "/release/<str:version>",
        ReleaseDetailView.as_view(),
    ),
    # releases
    path(
        BASE_PATH + "/releases",
        GetReleasesView.as_view(),
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
