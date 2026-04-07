from django.urls import path

from bridge.boat_charging.views import (
    location_view,
    session_start_stop,
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
        BASE_PATH + "/session/<str:charging_station_id>",
        session_start_stop.SessionStartStopView.as_view(),
        name="boat-charging-session-start-stop",
    ),
]
