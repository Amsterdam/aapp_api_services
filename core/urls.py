from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.urls import path

def get_swagger_paths(base_path):
    urlpatterns = [
        # drf-spectacular
        path(
            base_path + "/openapi/",
            SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[]),
            name="openapi-schema",
        ),
    ]

    if settings.DEBUG:
        urlpatterns += [
            path(
                base_path + "/apidocs",
                SpectacularSwaggerView.as_view(
                    url_name="openapi-schema", authentication_classes=[], permission_classes=[]
                ),
                name="swagger-ui",
            ),
        ]
    return urlpatterns
