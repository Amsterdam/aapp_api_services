from django.urls import path

from bridge.mijnamsterdam.views import (
    LogoutNotificationView,
    MijnAmsterdamAccessTokenView,
    MijnAmsterdamDeviceView,
)

urlpatterns = [
    path(
        "mijnamsterdam/api/v1/logout-notification",
        LogoutNotificationView.as_view(),
        name="mijn-amsterdam-logout-notification",
    ),
    path(
        "mijnamsterdam/api/v1/device",
        MijnAmsterdamDeviceView.as_view(),
        name="mijn-amsterdam-device",
    ),
    path(
        "mijnamsterdam/api/v1/access-token",
        MijnAmsterdamAccessTokenView.as_view(),
        name="mijn-amsterdam-access-token",
    ),
]
