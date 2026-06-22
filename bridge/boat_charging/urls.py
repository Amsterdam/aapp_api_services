from django.urls import path

from bridge.boat_charging.views import (
    location_view,
    login_view,
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
        BASE_PATH + "/oidc-settings",
        login_view.OIDCSettingsView.as_view(),
        name="boat-charging-oidc-settings",
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
        BASE_PATH + "/sessions/init",
        session_start_stop.SessionInitView.as_view(),
        name="boat-charging-session-init",
    ),
    path(
        BASE_PATH + "/sessions/<str:session_id>/start",
        session_start_stop.SessionStartView.as_view(),
        name="boat-charging-session-start",
    ),
    path(
        BASE_PATH + "/sessions/<str:session_id>/stop",
        session_start_stop.SessionStopView.as_view(),
        name="boat-charging-session-stop",
    ),
    path(
        BASE_PATH + "/terms",
        terms_view.TermsView.as_view(),
        name="boat-charging-terms",
    ),
]
