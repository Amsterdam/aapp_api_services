from django.conf import settings
from django.urls import path

from bridge.proxy.views import (
    AddressPostalAreaByCoordinateView,
    AddressSearchByCoordinateView,
    AddressSearchByNameView,
    AddressSearchView,
    EgisProxyExternalView,
    EgisProxyView,
    HealthCheckView,
    PollingStationsView,
    ServerTimeView,
)

urlpatterns = []
if settings.ENVIRONMENT_SLUG in ["o", "t"]:
    urlpatterns += [
        # egis dev proxy
        path(
            "parking/api/v1/egis-proxy/<path:path>",
            EgisProxyView.as_view(),
            name="egis-proxy",
        ),
        path(
            "parking/api/v1/egis-ext-proxy/<path:path>",
            EgisProxyExternalView.as_view(),
            name="egis-ext-proxy",
        ),
    ]

urlpatterns += [
    # health check
    path(
        "bridge/api/v1/health-check",
        HealthCheckView.as_view(),
        name="health-check",
    ),
    # server time
    path(
        "bridge/api/v1/time",
        ServerTimeView.as_view(),
        name="server-time",
    ),
    # election locations
    path(
        "elections/api/v1/polling-stations",
        PollingStationsView.as_view(),
        name="elections-polling-stations",
    ),
    # address search
    path(
        "address/api/v1/free",
        AddressSearchView.as_view(),
        name="address-search",
    ),
    path(
        "address/api/v1/address",
        AddressSearchByNameView.as_view(),
        name="address-search-by-name",
    ),
    path(
        "address/api/v1/coordinate",
        AddressSearchByCoordinateView.as_view(),
        name="address-search-by-coordinate",
    ),
    path(
        "address/api/v1/postal_area",
        AddressPostalAreaByCoordinateView.as_view(),
        name="address-postal-area-by-coordinate",
    ),
]
