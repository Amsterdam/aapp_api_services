from django.urls import path

from bridge.mijnamsterdam.views import (
    LogoutNotificationView,
    MijnAmsterdamDeviceView,
    MijnAmsterdamThemesDetailView,
    MijnAmsterdamThemesView,
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
        "mijnamsterdam/api/v1/themes",
        MijnAmsterdamThemesView.as_view(),
        name="mijn-amsterdam-themes",
    ),
    path(
        "mijnamsterdam/api/v1/themes/<str:service_name>",
        MijnAmsterdamThemesDetailView.as_view(),
        name="mijn-amsterdam-themes-detail",
    ),
]
