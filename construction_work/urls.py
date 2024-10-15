from django.urls import path

import construction_work.views.article_view
from construction_work.views import device_views, project_views
from core.urls import get_swagger_paths

BASE_PATH = "construction-work/api/v1"

urlpatterns = [
    # projects
    path(
        BASE_PATH + "/projects",
        project_views.ProjectListView.as_view(),
        name="construction-work-project-list",
    ),
    path(
        BASE_PATH + "/projects/details",
        project_views.ProjectDetailsView.as_view(),
        name="construction-work-get-project",
    ),
    path(
        BASE_PATH + "/projects/search",
        project_views.ProjectSearchView.as_view(),
        name="construction-work-project-search",
    ),
    path(
        BASE_PATH + "/projects/follow",
        project_views.FollowProjectView.as_view(),
        name="construction-work-follow-project",
    ),
    path(
        BASE_PATH + "/projects/followed/articles",
        project_views.FollowedProjectsArticlesView.as_view(),
        name="followed-projects-with-articles",
    ),
    path(
        BASE_PATH + "/projects/news",
        project_views.ArticleDetailView.as_view(),
        name="construction-work-get-article",
    ),
    path(
        BASE_PATH + "/projects/warning",
        project_views.WarningMessageDetailView.as_view(),
        name="construction-work-get-warning",
    ),
    # articles
    path(
        BASE_PATH + "/articles",
        construction_work.views.article_view.ArticleListView.as_view(),
        name="construction-work-article-list",
    ),
    # devices
    path(
        BASE_PATH + "/device/register",
        device_views.DeviceRegisterView.as_view(),
        name="construction-work-register-device",
    ),
]
urlpatterns += get_swagger_paths(BASE_PATH)
