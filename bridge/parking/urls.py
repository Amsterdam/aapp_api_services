from django.urls import path

from bridge.parking.views import account_views, license_plate_views, session_views

urlpatterns = [
    path(
        "parking/api/v1/login",
        account_views.ParkingAccountLoginView.as_view(),
        name="parking-account-login",
    ),
    path(
        "parking/api/v1/account-details",
        account_views.ParkingAccountDetailsView.as_view(),
        name="parking-account-details",
    ),
    path(
        "parking/api/v1/pin-code",
        account_views.ParkingRequestPinCodeView.as_view(),
        name="parking-request-pin-code",
    ),
    path(
        "parking/api/v1/permits",
        account_views.ParkingPermitsView.as_view(),
        name="parking-permits",
    ),
    path(
        "parking/api/v1/balance",
        account_views.ParkingBalanceView.as_view(),
        name="parking-balance",
    ),
    path(
        "parking/api/v1/license-plates",
        license_plate_views.ParkingLicensePlateListView.as_view(),
        name="parking-license-plates-list",
    ),
    path(
        "parking/api/v1/license-plate",
        license_plate_views.ParkingLicensePlatePostDeleteView.as_view(),
        name="parking-license-plates-post-delete",
    ),
    path(
        "parking/api/v1/sessions",
        session_views.ParkingSessionListView.as_view(),
        name="parking-sessions",
    ),
    path(
        "parking/api/v1/session",
        session_views.ParkingSessionStartUpdateView.as_view(),
        name="parking-session-start-update",
    ),
    path(
        "parking/api/v1/session/receipt",
        session_views.ParkingSessionReceiptView.as_view(),
        name="parking-session-receipt",
    ),
]
