from django.urls import path

from bridge.sport.views import swim_views

BASE_PATH = "sport/api/v1"
urlpatterns = [
    path(
        BASE_PATH + "/swim/locations",
        swim_views.SwimLocationsView.as_view(),
        name="swim-locations",
    ),
    # path(
    #     BASE_PATH + "/swim/schedule",
    #     swim_views.SwimLocationsView.as_view(),
    #     name="swim-schedule",
    # ),
]
