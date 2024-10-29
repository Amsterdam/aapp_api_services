from django.conf import settings
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


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
        ]
    return urlpatterns
