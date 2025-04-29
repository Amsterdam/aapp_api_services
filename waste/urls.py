from django.urls import path

from core.urls import get_swagger_paths
from waste.views.container_views import WasteContainerPassNumberView
from waste.views.notification_views import WasteGuideNotificationView
from waste.views.waste_views import WasteGuideView

BASE_PATH = "waste/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/guide",
        WasteGuideView.as_view(),
        name="waste-guide-calendar",
    ),
    path(
        BASE_PATH + "/guide/notification",
        WasteGuideNotificationView.as_view(),
        name="waste-guide-notification",
    ),
    # container-pass
    path(
        BASE_PATH + "/container/pass-number",
        WasteContainerPassNumberView.as_view(),
        name="waste-container-pass-number",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
