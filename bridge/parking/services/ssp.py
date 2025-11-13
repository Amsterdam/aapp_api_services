import logging
from enum import Enum

from django.conf import settings

logger = logging.getLogger(__name__)


class SSPEndpoint(Enum):
    # Account
    LOGIN = f"{settings.SSP_BASE_URL_V2}/api/ssp/login_check"
    PERMITS = f"{settings.SSP_BASE_URL_V2}/api/v1/permit_overview/product_list"
    PERMIT = f"{settings.SSP_BASE_URL_V2}/api/v1/client_product/{{permit_id}}"
    PAID_PARKING_ZONE = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/paid_parking_zone/list/client_product/{{permit_id}}"

    # Transactions
    TRANSACTIONS = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/wallet_transaction/list"  # page=1&row_per_page=10&sort=paid_at:desc&filters[status]=COMPLETED

    # Visitor
    VISITOR_CREATE = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/client_product/{{permit_id}}/visitor_account/create"  # POST
    VISITOR_DELETE = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/client_product/{{permit_id}}/visitor_account/deactivate"  # POST
    VISITOR_ALLOCATE = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/client_product/{{permit_id}}/time_balance/allocate"  # POST {amount: 2} hrs
    VISITOR_DEALLOCATE = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/client_product/{{permit_id}}/time_balance/withdraw"  # POST {amount: 1} hrs

    # License plates
    LICENSE_PLATES = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/favorite_vrn/list"
    LICENSE_PLATE_ADD = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/favorite_vrn/add"  # POST {vrn: "CD234D", description: "Secondary vehicle"}
    LICENSE_PLATE_DELETE = f"{settings.SSP_BASE_URL_V2}/api/v1/ssp/favorite_vrn/{{license_plate_id}}/delete"  # DELETE


class SSPEndpointExternal(Enum):
    # Account
    LOGIN = f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/login"

    # Sessions
    PARKING_SESSION_START = (
        f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/parking_session/start"
    )
    PARKING_SESSIONS = (
        f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/parking_session/list"
    )
    PARKING_SESSION_ACTIVATE = f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/parking_session/activate"  # POST {"report_code": 1004 ,"vrn":"AB124C"}
    PARKING_SESSION_EDIT = f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/parking_session/{{session_id}}/edit"  # PATCH {new_ended_at: "2025-09-13T08:45:00.000+00:00"}
    PARKING_SESSION_RECEIPT = f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/parking_session/cost_calculator"  # POST {"client_product_id":10001,"ended_at":"Tue, 09 Sep 2025 22:30:00 GMT","started_at":"Tue, 09 Sep 2025 22:00:00 GMT","paid_parking_zone_id":37} OF ,"machine_number":10741
    PARKING_ZONE_BY_MACHINE = f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/paid_parking_zone/get_by_machine_number"  # POST {"client_product_id":1004,"machine_number":10741}

    # Transactions
    RECHARGE = f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/wallet_transaction/new"
    RECHARGE_CONFIRM = (
        f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/wallet_transaction/confirmation"
    )
    RECHARGE_CONFIRM_VISITOR = f"{settings.SSP_BASE_URL_EXTERNAL}/api/v1/ssp/parking_session/visitor/confirmation"

    # Visitor
    # License plates

    # Parking Machines
    PARKING_MACHINES_LIST = (
        "https://nprverkooppunten.rdw.nl/Productie/verkooppunten.txt"
    )
