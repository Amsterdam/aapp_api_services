from django.conf import settings
from django.urls import path
from drf_spectacular.views import SpectacularSwaggerView

from contact.views import contact_views, link_views
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
]
urlpatterns += get_swagger_paths(BASE_PATH)


if settings.DEBUG:
    urlpatterns += [
        path(
            BASE_PATH + "apidocs/",
            SpectacularSwaggerView.as_view(
                url_name="module-openapi-schema",
                authentication_classes=[],
                permission_classes=[],
            ),
            name="module-swagger-ui",
        )
    ]
