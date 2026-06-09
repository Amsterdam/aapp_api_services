from django.urls import path

from bridge.boat_charging.views import (
    location_view,
    login_view,
    oidc_settings_view,
    session_start_stop,
    session_view,
    terms_view,
)

BASE_PATH = "boat-charging/api/v1"
urlpatterns = [
    path(
        BASE_PATH + "/login/guest",
        login_view.GuestLoginView.as_view(),
        name="boat-charging-guest-login",
    ),
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
    path(
        BASE_PATH + "/terms",
        terms_view.TermsView.as_view(),
        name="boat-charging-terms",
    ),
    path(
        BASE_PATH + "/oidc-settings",
        oidc_settings_view.OIDCSettingsView.as_view(),
        name="boat-charging-oidc-settings",
    ),
]
