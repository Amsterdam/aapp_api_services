from django.urls import path

from bridge.views.proxy_views import AddressSearchView, WasteGuideView
from bridge.views.waste_pass_views import WastePassNumberView
from core.urls import get_swagger_paths

BASE_PATH = "bridge/api/v1"

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
    # waste pass number
    path(
        "waste-container/api/v1/pass-number",
        WastePassNumberView.as_view(),
        name="waste-container-pass-number",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
