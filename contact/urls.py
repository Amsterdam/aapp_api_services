from django.contrib import admin
from django.urls import path

from contact.views import contact_views, link_views
from core.urls import get_swagger_paths
from core.views.admin_views import AdminLoginView

BASE_PATH = "contact/api/v1"


urlpatterns = [
    path(
        BASE_PATH + "/city-offices",
        contact_views.CityOfficesView.as_view(),
        name="contact-city-offices",
    ),
    path(BASE_PATH + "/links", link_views.LinksView.as_view(), name="contact-links"),
    path(
        BASE_PATH + "/health-check",
        contact_views.HealthCheckView.as_view(),
        name="contact-health-check",
    ),
    path(
        "contact/admin/login/",
        AdminLoginView.as_view(),
        name="contact-admin-login",
    ),
    path("contact/admin/", admin.site.urls),
]

urlpatterns += get_swagger_paths(BASE_PATH)
