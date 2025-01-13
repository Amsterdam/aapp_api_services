from django.conf import settings
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from bridge.views.proxy_views import AddressSearchView, WasteGuideView
from bridge.views.waste_pass_views import WastePassNumberView

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
    # address search
    path(
        "address/api/v1/free",
        AddressSearchView.as_view(),
        name="address-search",
    ),
    # waste pass number
    path(
        "waste/api/v1/pass-number",
        WastePassNumberView.as_view(),
        name="waste-pass-number",
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
