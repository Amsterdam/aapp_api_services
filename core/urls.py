from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.views import admin_views


def get_swagger_paths(base_path):
    service_name = base_path.split("/")[0]
    urlpatterns = [
        path(
            base_path + "/openapi/",
            SpectacularAPIView.as_view(
                authentication_classes=[], permission_classes=[]
            ),
            name=f"{service_name}-openapi-schema",
        ),
    ]

    if settings.DEBUG:
        urlpatterns += [
            path(
                base_path + "/apidocs/",
                SpectacularSwaggerView.as_view(
                    url_name=f"{service_name}-openapi-schema",
                    authentication_classes=[],
                    permission_classes=[],
                ),
                name=f"{service_name}-swagger-ui",
            ),
        ] + debug_toolbar_urls()
    return urlpatterns


def get_admin_paths(
    base_path_admin,
    enable_oidc=True,
):  # pragma: no cover
    service_name = base_path_admin.split("/")[0]
    urlpatterns = []

    if enable_oidc:
        urlpatterns += [
            path(base_path_admin + "/oidc/", include("mozilla_django_oidc.urls")),
            path(
                base_path_admin + "/login/",
                RedirectView.as_view(
                    pattern_name="oidc_authentication_init", permanent=False
                ),
                name=f"{service_name}-admin-login",
            ),
            path(
                base_path_admin + "/login/failure/",
                admin_views.OIDCLoginFailureView.as_view(),
                name=f"{service_name}-admin-login-failure",
            ),
        ]
    else:
        urlpatterns += [
            path(
                base_path_admin + "/login/",
                admin_views.AdminLoginView.as_view(),
                name=f"{service_name}-admin-login",
            ),
        ]

    # Admin has to be last, so that it can handle the login/failure paths
    urlpatterns += [
        path(base_path_admin + "/", admin.site.urls),
    ]

    return urlpatterns
