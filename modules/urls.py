from django.contrib import admin
from django.urls import path

from core.urls import get_swagger_paths
from core.views.admin_views import AdminLoginView
from modules.views import ReleaseDetailView

BASE_PATH = "modules/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/release/<str:version>",
        ReleaseDetailView.as_view(),
        name="modules-release-detail",
    ),
    path("modules/admin/", admin.site.urls),
    # Activate admin
    path(
        "modules/admin/login/",
        AdminLoginView.as_view(),
        name="modules-admin-login",
    ),
    path("modules/admin/", admin.site.urls),
]

urlpatterns += get_swagger_paths(BASE_PATH)
