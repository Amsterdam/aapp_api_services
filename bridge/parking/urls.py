from django.urls import path

from bridge.parking.views import (
    account_views,
    license_plate_views,
    parking_machine_views,
    permit_views,
    session_views,
    transaction_views,
    visitor_views,
)


def sessions_history_view(request, *args, **kwargs):
    query_params = request.GET.copy()
    query_params["status"] = "COMPLETED"
    request.GET = query_params
    view = session_views.ParkingSessionListView.as_view()
    return view(request, *args, **kwargs)


urlpatterns = [
    # Account
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
    # "parking/api/v1/pin-code",  # DEPRECATED
    # Permits
    path(
        "parking/api/v1/permits",
        permit_views.ParkingPermitsView.as_view(),
        name="parking-permits",
    ),
    path(
        "parking/api/v1/permit/<int:permit_id>/zones",
        permit_views.ParkingPermitZoneView.as_view(),
        name="parking-permit-zone",
    ),
    path(
        "parking/api/v1/permit/<int:permit_id>/zone_by_machine/<int:parking_machine_id>",
        permit_views.ParkingPermitZoneByMachineView.as_view(),
        name="parking-permit-zone-by-machine",
    ),
    # Sessions
    path(
        "parking/api/v1/session",
        session_views.ParkingSessionStartUpdateDeleteView.as_view(),
        name="parking-session-start-update-delete",
    ),
    path(
        "parking/api/v1/session/activate",
        session_views.ParkingSessionActivateView.as_view(),
        name="parking-session-activate",
    ),
    path(
        "parking/api/v1/session/receipt",
        session_views.ParkingSessionReceiptView.as_view(),
        name="parking-session-receipt",
    ),
    path(
        "parking/api/v1/sessions",
        session_views.ParkingSessionListView.as_view(),
        name="parking-sessions",
    ),
    path(
        "parking/api/v1/sessions/history",
        session_views.ParkingSessionListView.as_view(),
        {"status": "COMPLETED"},
        name="parking-session-history",
    ),
    # Transactions
    path(
        "parking/api/v1/balance",
        transaction_views.TransactionsBalanceView.as_view(),
        name="parking-balance",
    ),
    path(
        "parking/api/v1/balance-confirm",
        transaction_views.TransactionsBalanceConfirmView.as_view(),
        name="parking-balance-confirm",
    ),
    path(
        "parking/api/v1/transactions",
        transaction_views.TransactionsListView.as_view(),
        name="parking-transactions",
    ),
    # License plates
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
        "parking/api/v1/permit/<int:permit_id>/visitor",
        visitor_views.ParkingVisitorView.as_view(),
        name="parking-visitor-post-delete",
    ),
    path(
        "parking/api/v1/visitor/time-balance",
        visitor_views.ParkingVisitorTimeBalanceView.as_view(),
        name="parking-visitor-time-balance",
    ),
    path(
        "parking/api/v1/visitor/sessions",
        session_views.ParkingSessionVisitorListView.as_view(),
        name="parking-visitor-sessions",
    ),
    # "parking/api/v1/visitor/pin-code",  # DEPRECATED
    # Parking machines
    path(
        "parking/api/v1/parking-machines",
        parking_machine_views.ParkingMachineListView.as_view(),
        name="parking-machines-list",
    ),
]
