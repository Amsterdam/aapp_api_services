from bridge.views import WasteGuideView, AddressSearchView
from django.conf import settings
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # drf-spectacular
    path(
        "bridge/api/v1/openapi/",
        SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[]),
        name="bridge-openapi-schema",
    ),
    # afvalwijzer
    path(
        "waste-guide/api/v1/search",
        WasteGuideView.as_view(),
        name="waste-guide-search",
    ),
    # Adres zoeker
    path(
        "address/api/v1/free",
        AddressSearchView.as_view(),
        name="address-search",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "bridge/api/v1/apidocs",
            SpectacularSwaggerView.as_view(
                url_name="bridge-openapi-schema",
                authentication_classes=[],
                permission_classes=[],
            ),
            name="bridge-swagger-ui",
        )
    ]
