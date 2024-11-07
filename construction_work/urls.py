from django.urls import include, path

from construction_work.views import (
    article_view,
    device_views,
    manage_views,
    project_views,
)
from core.urls import get_swagger_paths

BASE_PATH = "construction-work/api/v1"


_urlpatterns = [
    # project lists
    path(
        "projects",
        project_views.ProjectListView.as_view(),
        name="project-list",
    ),
    path(
        "projects/search",
        project_views.ProjectSearchView.as_view(),
        name="project-search",
    ),
    # project details
    path(
        "project/details",
        project_views.ProjectDetailsView.as_view(),
        name="get-project",
    ),
    # project actions
    path(
        "projects/follow",
        project_views.FollowProjectView.as_view(),
        name="follow-project",
    ),
    # news (articles & warnings)
    path(
        "articles",
        article_view.ArticleListView.as_view(),
        name="article-list",
    ),
    path(
        "projects/followed/articles",
        project_views.FollowedProjectsArticlesView.as_view(),
        name="followed-projects-with-articles",
    ),
    path(
        "project/news",
        project_views.ArticleDetailView.as_view(),
        name="get-article",
    ),
    path(
        "project/warning",
        project_views.WarningMessageDetailView.as_view(),
        name="get-warning",
    ),
    # devices
    path(
        "device/register",
        device_views.DeviceRegisterView.as_view(),
        name="register-device",
    ),
    # manage publishers
    path(
        "manage/publishers",
        manage_views.PublisherListCreateView.as_view(),
        name="manage-publisher-list-create",
    ),
    path(
        "manage/publishers/<int:pk>",
        manage_views.PublisherDetailView.as_view(),
        name="manage-publisher-read-update-delete",
    ),
    path(
        "manage/publishers/<int:pk>/projects",
        manage_views.PublisherAssignProjectView.as_view(),
        name="manage-publisher-assign-project",
    ),
    path(
        "manage/publishers/<int:pk>/projects/<int:project_id>",
        manage_views.PublisherUnassignProjectView.as_view(),
        name="manage-publisher-unassign-project",
    ),
    # manage projects
    path(
        "manage/projects",
        manage_views.ProjectListForManageView.as_view(),
        name="manage-project-list",
    ),
    path(
        "manage/projects/<int:pk>",
        manage_views.ProjectDetailsForManageView.as_view(),
        name="manage-project-details",
    ),
    # manage warnings
    path(
        "manage/projects/<int:pk>/warnings",
        manage_views.WarningMessageCreateView.as_view(),
        name="manage-warning-create",
    ),
    path(
        "manage/warnings/<int:pk>",
        manage_views.WarningMessageDetailView.as_view(),
        name="manage-warning-read-update-delete",
    ),
    path("warning-image", manage_views.ImageUploadView.as_view(), name="image-upload"),
]

urlpatterns = [
    path(
        BASE_PATH + "/",
        include((_urlpatterns, "construction-work"), namespace="construction-work"),
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
