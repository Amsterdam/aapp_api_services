from django.urls import path

from contact.views import contact_views, link_views, survey_views
from core.urls import get_admin_paths, get_swagger_paths

BASE_PATH = "contact/api/v1"

BASE_PATH_API = "contact/api/v1"
BASE_PATH_ADMIN = "contact/admin"

urlpatterns = [
    path(
        BASE_PATH_API + "/city-offices",
        contact_views.CityOfficesView.as_view(),
        name="contact-city-offices",
    ),
    path(
        BASE_PATH_API + "/waiting-times",
        contact_views.WaitingTimesView.as_view(),
        name="contact-waiting-times",
    ),
    path(
        BASE_PATH_API + "/links", link_views.LinksView.as_view(), name="contact-links"
    ),
    path(
        BASE_PATH_API + "/health-check",
        contact_views.HealthCheckView.as_view(),
        name="contact-health-check",
    ),
    path(
        BASE_PATH + "/surveys",
        survey_views.SurveyView.as_view(),
        name="contact-surveys",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/versions",
        survey_views.SurveyVersionView.as_view(),
        name="contact-survey-versions",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/versions/<str:version>",
        survey_views.SurveyVersionDetailView.as_view(),
        name="contact-survey-version-detail",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/latest",
        survey_views.SurveyVersionLatestView.as_view(),
        name="contact-survey-version-latest",
    ),
    path(
        BASE_PATH + "/surveys/<str:unique_code>/versions/<str:version>/entries",
        survey_views.SurveyVersionEntryView.as_view(),
        name="contact-survey-version-entries",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH_API)
urlpatterns += get_admin_paths(BASE_PATH_ADMIN, enable_oidc=False)
