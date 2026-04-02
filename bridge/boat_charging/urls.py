from django.urls import path

from bridge.boat_charging.views import location_view

BASE_PATH = "boat-charging/api/v1"
urlpatterns = [
    path(
        BASE_PATH + "/locations",
        location_view.LocationView.as_view(),
        name="boat-charging-locations",
    ),
    path(
        BASE_PATH + "/locations/<str:location_id>",
        location_view.LocationDetailView.as_view(),
        name="boat-charging-location-detail",
    ),
]
