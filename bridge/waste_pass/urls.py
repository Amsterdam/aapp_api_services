from django.urls import path

from bridge.waste_pass.views import WastePassNumberView

urlpatterns = [
    path(
        "waste-container/api/v1/pass-number",
        WastePassNumberView.as_view(),
        name="waste-container-pass-number",
    ),
]
