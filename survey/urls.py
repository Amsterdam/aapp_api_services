from django.urls import path

from core.urls import get_admin_paths, get_swagger_paths
from survey import views

BASE_PATH = "survey/api/v1"
BASE_PATH_ADMIN = "survey/admin"

urlpatterns = [
    path(
        BASE_PATH + "/surveys",
        views.SurveyView.as_view(),
        name="survey-surveys",
    ),
    path(
        BASE_PATH + "/config/<str:location>",
        views.SurveyConfigView.as_view(),
        name="survey-config",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/versions",
        views.SurveyVersionView.as_view(),
        name="survey-versions",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/versions/<str:version>",
        views.SurveyVersionDetailView.as_view(),
        name="survey-version-detail",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/latest",
        views.SurveyVersionLatestView.as_view(),
        name="survey-version-latest",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/versions/<str:version>/entries",
        views.SurveyVersionEntryView.as_view(),
        name="survey-version-entries",
    ),
    path(
        BASE_PATH + "/surveys/entries",
        views.SurveyVersionEntryListView.as_view(),
        name="survey-entries-list",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
urlpatterns += get_admin_paths(BASE_PATH_ADMIN, enable_oidc=False)
