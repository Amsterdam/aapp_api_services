from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from city_pass.views import data_views, session_views

# from rest_framework.permissions import AllowAny


urlpatterns = [
    # drf-spectacular
    path(
        "openapi/",
        SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[]),
        name="schema",
    ),
    path(
        "apidocs/",
        SpectacularSwaggerView.as_view(
            url_name="schema", authentication_classes=[], permission_classes=[]
        ),
        name="swagger-ui",
    ),
    # session
    path("session/init", session_views.SessionInitView.as_view(), name="init-session"),
    path(
        "session/credentials",
        session_views.SessionPostCredentialView.as_view(),
        name="post-city-pass-credentials",
    ),
    path(
        "session/refresh",
        session_views.SessionRefreshAccessView.as_view(),
        name="refresh-access",
    ),
    # data
    path("data/passes", data_views.PassesDataView.as_view(), name="passes-data"),
]
