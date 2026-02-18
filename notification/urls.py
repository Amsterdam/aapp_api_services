from django.urls import path

from core.urls import get_swagger_paths
from notification.views import (
    device_views,
    notification_views,
)

BASE_PATH = "notification/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/device/register",
        device_views.DeviceRegisterView.as_view(),
        name="notification-register-device",
    ),
    path(
        BASE_PATH + "/device/disabled_push_type",
        device_views.NotificationPushTypeDisabledView.as_view(),
        name="notification-device-push-type-disabled",
    ),
    path(
        BASE_PATH + "/device/disabled_push_types",
        device_views.NotificationPushTypeDisabledListView.as_view(),
        name="notification-device-push-type-disabled-list",
    ),
    path(
        BASE_PATH + "/device/disabled_push_module",
        device_views.NotificationPushModuleDisabledView.as_view(),
        name="notification-device-push-module-disabled",
    ),
    path(
        BASE_PATH + "/device/disabled_push_modules",
        device_views.NotificationPushModuleDisabledListView.as_view(),
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
        BASE_PATH + "/modules",
        notification_views.NotificationModulesView.as_view(),
        name="notification-modules",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
