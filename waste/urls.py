from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from core.urls import get_admin_paths, get_swagger_paths
from waste.views.container_views import WasteContainerPassNumberView
from waste.views.recycle_views import RecycleLocationsView
from waste.views.waste_views import (
    WasteGuideCalendarIcsView,
    WasteGuidePDFView,
    WasteGuideView,
)

BASE_PATH = "waste/api/v1"
BASE_PATH_ADMIN = "waste/admin"

urlpatterns = [
    path(
        BASE_PATH + "/guide",
        WasteGuideView.as_view(),
        name="waste-guide-calendar",
    ),
    path(
        BASE_PATH + "/guide/pdf",
        WasteGuidePDFView.as_view(),
        name="waste-guide-calendar-pdf",
    ),
    path(
        BASE_PATH + "/guide/<str:bag_nummeraanduiding_id>.ics",
        WasteGuideCalendarIcsView.as_view(),
        name="waste-guide-calendar-ics",
    ),
    # container-pass
    path(
        BASE_PATH + "/container/pass-number",
        WasteContainerPassNumberView.as_view(),
        name="waste-container-pass-number",
    ),
    # recycle locations
    path(
        BASE_PATH + "/recycle-locations",
        RecycleLocationsView.as_view(),
        name="waste-recycle-locations",
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += get_swagger_paths(BASE_PATH)
urlpatterns += get_admin_paths(BASE_PATH_ADMIN, enable_oidc=False)
