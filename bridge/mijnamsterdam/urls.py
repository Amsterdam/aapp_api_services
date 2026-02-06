from django.urls import path

from bridge.mijnamsterdam.views import MijnAmsterdamDeviceView

urlpatterns = [
    path(
        "mijnamsterdam/api/v1/device",
        MijnAmsterdamDeviceView.as_view(),
        name="mijn-amsterdam-device",
    )
]
