from django.contrib import admin
from django.urls import path

from core.urls import get_swagger_paths
from core.views.admin_views import AdminLoginView
from survey import views

BASE_PATH = "survey/api/v1"


urlpatterns = [
    path(
        BASE_PATH + "/surveys",
        views.SurveyView.as_view(),
        name="survey-surveys",
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
        "survey/admin/login/",
        AdminLoginView.as_view(),
        name="survey-admin-login",
    ),
    path("survey/admin/", admin.site.urls),
]

urlpatterns += get_swagger_paths(BASE_PATH)
