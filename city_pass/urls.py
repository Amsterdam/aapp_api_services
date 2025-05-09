from django.urls import path

from city_pass.views import data_views, session_views
from core.urls import get_swagger_paths

BASE_PATH = "city-pass/api/v1"

urlpatterns = [
    # session
    path(
        BASE_PATH + "/session/init",
        session_views.SessionInitView.as_view(),
        name="city-pass-session-init",
    ),
    path(
        BASE_PATH + "/session/credentials",
        session_views.SessionPostCredentialView.as_view(),
        name="city-pass-session-credentials",
    ),
    path(
        BASE_PATH + "/session/refresh",
        session_views.SessionRefreshAccessView.as_view(),
        name="city-pass-session-refresh",
    ),
    path(
        BASE_PATH + "/session/logout",
        session_views.SessionLogoutView.as_view(),
        name="city-pass-session-logout",
    ),
    path(
        BASE_PATH + "/session/logout",
        session_views.SessionLogoutView.as_view(),
        name="session-logout",
    ),
    # data
    path(
        BASE_PATH + "/data/passes",
        data_views.PassesDataView.as_view(),
        name="city-pass-data-passes",
    ),
    path(
        BASE_PATH + "/data/budget-transactions",
        data_views.BudgetTransactionsView.as_view(),
        name="city-pass-data-budget-transactions",
    ),
    path(
        BASE_PATH + "/data/aanbieding-transactions",
        data_views.AanbiedingTransactionsView.as_view(),
        name="city-pass-data-aanbieding-transactions",
    ),
    path(
        BASE_PATH + "/data/passes/block/<str:pass_number>",
        data_views.PassBlockView.as_view(),
        name="city-pass-data-pass-block",
    ),
]

urlpatterns += get_swagger_paths(BASE_PATH)
