import json
import logging
from enum import Enum

import requests
from django.conf import settings

from bridge.parking import exceptions

logger = logging.getLogger(__name__)


class SSPEndpoint(Enum):
    LOGIN = f"{settings.SSP_BASE_URL}/rest/sspapi/v1/login"
    PERMITS = f"{settings.SSP_BASE_URL}/rest/sspapi/v1/permits"
    LICENSE_PLATES = f"{settings.SSP_BASE_URL}/rest/sspapi/v1/licenseplates"
    CHANGE_PIN_CODE = f"{settings.SSP_BASE_URL}/rest/sspapi/v1/clients/pincode"
    REQUEST_PIN_CODE = f"{settings.SSP_BASE_URL}/rest/sspapi/v1/requestPinCode"
    PARKING_SESSIONS = f"{settings.SSP_BASE_URL}/rest/sspapi/v2/parkingsessions"
    PARKING_SESSION_RECEIPT = (
        f"{settings.SSP_BASE_URL}/rest/sspapi/v1/parkingsessions/receipt"
    )
    ORDERS = f"{settings.SSP_BASE_URL}/rest/sspapi/v1/orders"


def ssp_api_call(method, endpoint, data, ssp_access_token=None):
    """
    Make the call to the SSP API.
    Based on the method, the data is either passed as query params or as the body of the request.

    Args:
        method: The HTTP method to use.
        endpoint_name: The name of the endpoint to call.
        data: The data to send to the endpoint.
        ssp_access_token: The SSP access token to use.
    """
    query_params = None
    body_data = None
    if method == "get":
        query_params = data
    else:
        body_data = data

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if ssp_access_token:
        headers["Authorization"] = f"Bearer {ssp_access_token}"

    ssp_response = requests.request(
        method,
        endpoint.value,
        params=query_params,
        json=body_data,
        headers=headers,
    )

    if ssp_response.status_code == 200:
        return ssp_response

    if ssp_response.status_code == 400:
        try:
            ssp_response_json = json.loads(ssp_response.text)
        except json.JSONDecodeError:
            raise exceptions.SSPCallError(detail=ssp_response.text)

        ssp_response_error = ssp_response_json.get("error", {})
        ssp_response_content = ssp_response_error.get("content")
        # ssp_response_message = ssp_response_error.get("message")

        for error in exceptions.SSP_COMMON_400_ERRORS:
            if ssp_response_content and error.default_detail in ssp_response_content:
                raise error()
        raise exceptions.SSPCallError(detail=ssp_response.text)
    elif ssp_response.status_code == 401:
        raise exceptions.SSPForbiddenError(detail=ssp_response.text)
    elif ssp_response.status_code == 403:
        raise exceptions.SSPForbiddenError(detail=ssp_response.text)
    elif ssp_response.status_code == 404:
        raise exceptions.SSPNotFoundError(detail=ssp_response.text)
    else:
        logger.error(f"Unexpected SSP response: {ssp_response.text}")
        raise exceptions.SSPCallError(detail=ssp_response.text)
