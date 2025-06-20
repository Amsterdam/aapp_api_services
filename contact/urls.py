from django.urls import path

from contact.views import contact_views, link_views
from core.urls import get_admin_paths, get_swagger_paths

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
]

urlpatterns += get_swagger_paths(BASE_PATH_API)
urlpatterns += get_admin_paths(BASE_PATH_ADMIN)
