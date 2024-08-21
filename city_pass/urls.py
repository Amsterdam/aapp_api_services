from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from city_pass.views import data_views, session_views
from django.conf import settings

urlpatterns = [
    # drf-spectacular
    path(
        "openapi/",
        SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[]),
        name="schema",
    ),
    # session
    path(
        "session/init", session_views.SessionInitView.as_view(),
        name="city-pass-session-init",
    ),
    path(
        "session/credentials",
        session_views.SessionPostCredentialView.as_view(),
        name="city-pass-session-credentials",
    ),
    path(
        "session/refresh",
        session_views.SessionRefreshAccessView.as_view(),
        name="city-pass-session-refresh",
    ),
    path(
        "session/logout",
        session_views.SessionLogoutView.as_view(),
        name="city-pass-session-logout",
    ),
    # data
    path(
        "data/passes", data_views.PassesDataView.as_view(),
        name="city-pass-data-passes",
    ),
    path(
        "data/budget-transactions",
        data_views.BudgetTransactionsView.as_view(),
        name="city-pass-data-budget-transactions",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "apidocs/",
            SpectacularSwaggerView.as_view(
                url_name="schema", authentication_classes=[], permission_classes=[]
            ),
            name="city-pass-swagger-ui",
        )
    ]