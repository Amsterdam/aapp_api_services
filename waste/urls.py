from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core.urls import get_swagger_paths
from core.views.admin_views import AdminLoginView
from waste.views.container_views import WasteContainerPassNumberView
from waste.views.notification_views import (
    WasteNotificationCreateView,
    WasteNotificationDetailView,
)
from waste.views.recycle_views import RecycleLocationsView
from waste.views.waste_views import WasteGuideCalendarIcsView, WasteGuideView

BASE_PATH = "waste/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/guide",
        WasteGuideView.as_view(),
        name="waste-guide-calendar",
    ),
    path(
        BASE_PATH + "/guide/<str:bag_nummeraanduiding_id>.ics",
        WasteGuideCalendarIcsView.as_view(),
        name="waste-guide-calendar-ics",
    ),
    path(
        BASE_PATH + "/guide/notifications",
        WasteNotificationCreateView.as_view(),
        name="waste-guide-notification-create",
    ),
    path(
        BASE_PATH + "/guide/notification",
        WasteNotificationDetailView.as_view(),
        name="waste-guide-notification-detail",
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
    # Activate admin
    path(
        "waste/admin/login/",
        AdminLoginView.as_view(),
        name="waste-admin-login",
    ),
    path("waste/admin/", admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += get_swagger_paths(BASE_PATH)
