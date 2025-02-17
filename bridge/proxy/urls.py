from django.urls import path

from bridge.proxy.views import AddressSearchView, WasteGuideView

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
]
