import logging
from collections import defaultdict

import httpx
from django.conf import settings
from rest_framework.exceptions import NotAuthenticated
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.boat_charging.client import client
from bridge.boat_charging.exceptions import (
    BoatChargingServerError,
)
from core.utils.caching_utils import cache_function

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True,  # reraise error after retries are exhausted
)
async def make_request(
    self,
    *,
    endpoint,
    headers,
    method,
    body_data=None,
    query_params=None,
    auth=None,
    data=None,
):
    assert not (body_data and data), (
        "Either body_data or data must be provided, not both"
    )
    response = await client.request(
        method=method,
        url=endpoint,
        params=query_params,
        json=body_data,  # json payload
        data=data,  # for form data
        headers=headers,
        auth=auth,
    )
    if response.is_success:
        return response.json()
    return await self.raise_exception(response)


async def api_call(
    method,
    endpoint,
    access_token=None,
    body_data=None,
    query_params=None,
    requires_access_token=True,
    paginated=True,
):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",  # necessary to get through WAF
        # "X-Auth-Token": settings.API_KEY,
    }
    if requires_access_token:
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        else:
            raise NotAuthenticated("No access token provided in request headers")

    try:
        payload = await make_request(
            method=method,
            endpoint=endpoint,
            headers=headers,
            query_params=query_params,
            body_data=body_data,
        )
    except httpx.HTTPError as exc:
        logger.warning(
            "Request failed before response (%s)",
            type(exc).__name__,
            exc_info=True,
        )
        raise BoatChargingServerError("Request failed before response") from exc

    if paginated:
        return payload["content"]
    return payload


@cache_function(timeout=60)
async def get_charging_station_statuses() -> dict:
    """
    Fetch all charging status data and construct a mapping of location IDs with
    a summary of the charging station statusses. This allows users to see if a
    location has available charging stations.

    There are three possible status values for a charging station:
    - "OPERATIVE": The charging station is available for use. (at least one station at the location is available)
    - "OCCUPIED": The charging station is currently in use and not available (all stations at the location are occupied).
    - "INOPERATIVE": The charging station is not operational and cannot be used (there is no station available and at least one station is out of order).
    """
    endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}"
    data = await api_call("get", endpoint=endpoint)
    pre_status_mapping = defaultdict(list)
    for item in data:
        location_id = item["locationId"]
        pre_status_mapping[location_id].append(item["status"])

    status_mapping = {}
    for location in pre_status_mapping:
        if "OPERATIVE" in pre_status_mapping[location]:
            status_mapping[location] = "OPERATIVE"
        elif (
            "INOPERATIVE" in pre_status_mapping[location]
            or "OFFLINE" in pre_status_mapping[location]
            or "UNKNOWN" in pre_status_mapping[location]
        ):
            status_mapping[location] = "INOPERATIVE"
        else:
            status_mapping[location] = "OCCUPIED"
    return status_mapping
