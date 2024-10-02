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
    path(
        BASE_PATH + "/projects/search",
        project_views.ProjectSearchView.as_view(),
        name="project-search",
    ),
    path(
        BASE_PATH + "/projects/follow",
        project_views.FollowProjectView.as_view(),
        name="follow-project",
    ),
    path(
        BASE_PATH + "/projects/followed/articles",
        project_views.FollowedProjectsWithArticlesView.as_view(),
        name="followed-projects-with-articles",
    ),
]
