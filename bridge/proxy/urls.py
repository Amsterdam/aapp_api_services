from django.urls import path

from bridge.proxy.views import (
    AddressSearchByCoordinateView,
    AddressSearchByNameView,
    AddressSearchView,
    WasteGuideView,
)

urlpatterns = [
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
