from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from city_pass.views import session_views

urlpatterns = [
    # drf-spectacular
    path("apidocs/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "apidocs/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path('session/init/', session_views.SessionInitView.as_view(), name="session-init"),
]
