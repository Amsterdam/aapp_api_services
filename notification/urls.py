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
        BASE_PATH_INTERNAL + "/scheduled-notification",
        notification_internal_views.ScheduledNotificationView.as_view(
            {
                "post": "create",
                "get": "list",
            }
        ),
        name="notification-scheduled-notification",
    ),
    path(
        BASE_PATH_INTERNAL + "/scheduled-notification/<str:identifier>",
        notification_internal_views.ScheduledNotificationDetailView.as_view(),
        name="notification-scheduled-notification-detail",
    ),
    # EXTERNAL ENDPOINTS
    path(
        BASE_PATH + "/device/register",
        device_views.DeviceRegisterView.as_view(),
        name="notification-register-device",
    ),
    path(
        BASE_PATH + "/device/disabled_push_type",
        device_views.NotificationPushEnabledView.as_view(),
        name="notification-device-push-type-disabled",
    ),
    path(
        BASE_PATH + "/device/disabled_push_types",
        device_views.NotificationPushEnabledListView.as_view(),
        name="notification-device-push-type-disabled-list",
    ),
    path(
        BASE_PATH + "/device/disabled_push_module",
        device_views.NotificationPushModuleEnabledView.as_view(),
        name="notification-device-push-module-disabled",
    ),
    path(
        BASE_PATH + "/device/disabled_push_modules",
        device_views.NotificationPushModuleEnabledListView.as_view(),
        name="notification-device-push-module-disabled-list",
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
    path(
        BASE_PATH + "/notifications/last",
        notification_views.NotificationLastView.as_view(),
        name="notification-last",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
