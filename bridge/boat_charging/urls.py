from django.urls import path

from bridge.boat_charging.views import (
    charging_station_view,
    location_view,
    session_view,
)

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
    path(
        BASE_PATH + "/sessions",
        session_view.SessionView.as_view(),
        name="boat-charging-sessions",
    ),
    path(
        BASE_PATH + "/sessions/<str:session_id>",
        session_view.SessionDetailView.as_view(),
        name="boat-charging-session-detail",
    ),
    path(
        BASE_PATH + "/charging-station/<str:charging_station_id>",
        charging_station_view.ChargingStationView.as_view(),
        name="boat-charging-station-detail",
    ),
]
