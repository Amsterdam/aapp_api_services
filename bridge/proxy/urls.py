from django.urls import path

from bridge.proxy.views import (
    AddressSearchByCoordinateView,
    AddressSearchByNameView,
    AddressSearchView,
    EgisProxyExternalView,
    EgisProxyView,
    PollingStationsView,
    WasteGuideView,
)

urlpatterns = [
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
    # afvalwijzer
    path(
        "waste-guide/api/v1/search",
        WasteGuideView.as_view(),
        name="waste-guide-search",
    ),
    # election locations
    path(
        "polling-stations/api/v1/locations",
        PollingStationsView.as_view(),
        name="polling-stations",
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
]
