from django.urls import path

from core.urls import get_swagger_paths
from notification.views import (
    device_views,
    notification_internal_views,
    notification_views,
)

BASE_PATH = "notification/api/v1"
BASE_PATH_INTERNAL = "internal/api/v1"

urlpatterns = [
    # INTERNAL ENDPOINTS
    path(
        BASE_PATH_INTERNAL + "/notification",
        notification_internal_views.NotificationInitView.as_view(),
        name="notification-create-notification",
    ),
    path(
        BASE_PATH_INTERNAL + "/image",
        notification_internal_views.ImageSetCreateView.as_view(),
        name="notification-create-image",
    ),
    # EXTERNAL ENDPOINTS
    path(
        BASE_PATH + "/device/register",
        device_views.DeviceRegisterView.as_view(),
        name="notification-register-device",
    ),
    path(
        BASE_PATH + "/notifications/<uuid:notification_id>",
        notification_views.NotificationDetailView.as_view(),
        name="notification-detail-notification",
    ),
    path(
        BASE_PATH + "/notifications",
        notification_views.NotificationListView.as_view(),
        name="notification-list-notifications",
    ),
    path(
        BASE_PATH + "/notifications/mark_all_read",
        notification_views.NotificationMarkAllReadView.as_view(),
        name="notification-read-notifications",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
