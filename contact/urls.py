from django.urls import path

from contact.views import link_views


BASE_PATH = "contact/api/v1"

urlpatterns = [path(BASE_PATH + "/links", link_views.get_links, name="contact-links")]
