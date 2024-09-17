from django.urls import path

from contact.views import link_views
from core.urls import get_swagger_paths


BASE_PATH = "contact/api/v1"

urlpatterns = [path(BASE_PATH + "/links", link_views.LinksView.as_view(), name="contact-links")]
urlpatterns += get_swagger_paths(BASE_PATH)