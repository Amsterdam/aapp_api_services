from django.urls import path

from construction_work.views import project_views

BASE_PATH = "construction_work/api/v1"

urlpatterns = [
    path(
        BASE_PATH + "/projects",
        project_views.ProjectListView.as_view(),
        name="project-list",
    ),
    path(
        BASE_PATH + "/projects/details",
        project_views.ProjectDetailsView.as_view(),
        name="project-details",
    ),
]
