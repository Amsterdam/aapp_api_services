from django.urls import path

from bridge.sport.views import login_views, swim_views

BASE_PATH = "sport/api/v1"
urlpatterns = [
    path(
        BASE_PATH + "/swim/locations",
        swim_views.SwimLocationsView.as_view(),
        name="swim-locations",
    ),
    path(
        BASE_PATH + "/swim/login",
        login_views.SwimLoginView.as_view(),
        name="swim-login",
    ),
]
