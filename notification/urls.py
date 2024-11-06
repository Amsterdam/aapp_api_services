from django.urls import path

from core.urls import get_swagger_paths
from notification.views import client_views, notification_views

BASE_PATH = "notification/api/v1"
BASE_PATH_INTERNAL = "internal/api/v1"


urlpatterns = [
    path(
        "client/register",
        client_views.ClientRegisterView.as_view(),
        name="notification-register-client",
    ),
    path(
        BASE_PATH_INTERNAL + "/notification",
        notification_views.NotificationInitView.as_view(),
        name="notification-create-notification",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
