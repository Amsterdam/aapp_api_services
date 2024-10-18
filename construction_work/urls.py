from django.urls import include, path

import construction_work.views.article_view
from construction_work.views import device_views, manage_views, project_views
from core.urls import get_swagger_paths

BASE_PATH = "construction-work/api/v1/"

_urlpatterns = [
    # projects
    path(
        "projects",
        project_views.ProjectListView.as_view(),
        name="project-list",
    ),
    path(
        "projects/details",
        project_views.ProjectDetailsView.as_view(),
        name="get-project",
    ),
    path(
        "projects/search",
        project_views.ProjectSearchView.as_view(),
        name="project-search",
    ),
    path(
        "projects/follow",
        project_views.FollowProjectView.as_view(),
        name="follow-project",
    ),
    path(
        "projects/followed/articles",
        project_views.FollowedProjectsArticlesView.as_view(),
        name="followed-projects-with-articles",
    ),
    path(
        "projects/news",
        project_views.ArticleDetailView.as_view(),
        name="get-article",
    ),
    path(
        "projects/warning",
        project_views.WarningMessageDetailView.as_view(),
        name="get-warning",
    ),
    # articles
    path(
        "articles",
        construction_work.views.article_view.ArticleListView.as_view(),
        name="article-list",
    ),
    # devices
    path(
        "device/register",
        device_views.DeviceRegisterView.as_view(),
        name="register-device",
    ),
    # manage
    path(
        "manage/projects",
        manage_views.PublisherListCreateView.as_view(),
        name="manage-publisher-list-create",
    ),
    path(
        "manage/projects/<int:pk>",
        manage_views.PublisherDetailView.as_view(),
        name="manage-publisher-read-update-delete",
    ),
]

urlpatterns = [
    path(
        BASE_PATH,
        include((_urlpatterns, "construction_work"), namespace="construction-work"),
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
