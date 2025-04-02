from django.urls import path

from core.urls import get_swagger_paths
from waste.views.notification_views import WasteGuideNotificationView
from waste.views.waste_views import WasteCalendarView

BASE_PATH = "waste/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/calendar",
        WasteCalendarView.as_view(),
        name="waste-guide-calendar",
    ),
    path(
        BASE_PATH + "/notification",
        WasteGuideNotificationView.as_view(),
        name="waste-guide-notification",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
