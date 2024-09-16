""" Routes configuration
"""
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from modules.views import views_modules

schema_view = get_schema_view(
    openapi.Info(
        title="Amsterdam APP Module: Modules",
        default_version="v1",
        description="API backend server for: Modules",
    ),
    public=True,
    permission_classes=([permissions.AllowAny]),
)

""" Base path: /modules/api/v1
"""

urlpatterns = [
    # Swagger (drf-yasg framework)
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^apidocs/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    # End-points from https://amsterdam-app.stoplight.io/docs/amsterdam-app/
    path(
        "module/<str:slug>/version/<str:version>/status",
        csrf_exempt(views_modules.module_version_status),
    ),
    path(
        "module/<str:slug>/version/<str:version>",
        csrf_exempt(views_modules.module_version),
    ),
    path("module/<str:slug>/version", csrf_exempt(views_modules.module_version_post)),
    path("module", csrf_exempt(views_modules.module_post)),
    path("module/<str:slug>", csrf_exempt(views_modules.module)),
    path("modules/latest", csrf_exempt(views_modules.modules_latest)),
    path(
        "modules/available-for-release/<str:release_version>",
        csrf_exempt(views_modules.modules_available_for_release),
    ),
    path("release", csrf_exempt(views_modules.release_post)),
    path("release/<str:version>", csrf_exempt(views_modules.release)),
    path("releases", csrf_exempt(views_modules.get_releases)),
]
