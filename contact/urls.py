from django.contrib import admin
from django.urls import path

from contact.views import contact_views, link_views, service_views
from core.urls import get_admin_paths, get_swagger_paths
from core.views.admin_views import AdminLoginView

BASE_PATH_CONTACT = "contact/api/v1"
BASE_PATH_ADMIN = "contact/admin"
BASE_PATH_SERVICE = "service/api/v1"

urlpatterns = [
    path(
        BASE_PATH_CONTACT + "/city-offices",
        contact_views.CityOfficesView.as_view(),
        name="contact-city-offices",
    ),
    path(
        BASE_PATH_CONTACT + "/links",
        link_views.LinksView.as_view(),
        name="contact-links",
    ),
    path(
        BASE_PATH_CONTACT + "/links", link_views.LinksView.as_view(), name="contact-links"
    ),
    path(
        BASE_PATH_CONTACT + "/health-check",
        contact_views.HealthCheckView.as_view(),
        name="contact-health-check",
    ),
    path(
        "contact/admin/login/",
        AdminLoginView.as_view(),
        name="contact-admin-login",
    ),
    path("contact/admin/", admin.site.urls),
    path(
        BASE_PATH_SERVICE + "/maps/<int:service_id>",
        service_views.ServiceMapView.as_view(),
        name="service-map",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH_CONTACT)
urlpatterns += get_admin_paths(BASE_PATH_ADMIN, enable_oidc=False)
