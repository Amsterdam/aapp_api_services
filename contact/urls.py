from django.contrib import admin
from django.urls import include, path

from contact.views import admin_views, contact_views, link_views
from core.urls import get_swagger_paths

BASE_PATH = "contact/api/v1"


urlpatterns = [
    path(
        BASE_PATH + "/city-offices",
        contact_views.CityOfficesView.as_view(),
        name="contact-city-offices",
    ),
    path(
        BASE_PATH + "/waiting-times",
        contact_views.WaitingTimesView.as_view(),
        name="contact-waiting-times",
    ),
    path(BASE_PATH + "/links", link_views.LinksView.as_view(), name="contact-links"),
    path(
        BASE_PATH + "/health-check",
        contact_views.HealthCheckView.as_view(),
        name="contact-health-check",
    ),
    path("contact/oidc/", include("mozilla_django_oidc.urls")),
    path("contact/admin/login/", admin_views.oidc_login, name="contact-admin-login"),
    path(
        "contact/admin/login/failure/",
        admin_views.oidc_login_failure,
        name="contact-admin-login-failure",
    ),
    path("contact/admin/", admin.site.urls),
]

urlpatterns += get_swagger_paths(BASE_PATH)
