import logging
import re
from urllib.parse import quote as urllib_parse_quote

import httpx
from adrf.generics import GenericAPIView
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.exceptions import NotAuthenticated, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.boat_charging.client import client
from bridge.boat_charging.exceptions import (
    BoatChargingAuthError,
    BoatChargingClientError,
    BoatChargingForbiddenError,
    BoatChargingMissingAccessToken,
    BoatChargingServerError,
)
from bridge.utils import max_or_none
from core.utils.caching_utils import cache_function
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)
PATH_PARAM_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class BaseView(GenericAPIView):
    serializer_class = None
    response_serializer_class = None
    requires_access_token = False
    paginated = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.location_status_kw_mapping = None

    async def api_call(
        self,
        method,
        endpoint,
        body_data=None,
        query_params=None,
        requires_access_token=True,
        paginated=False,
    ):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",  # necessary to get through WAF
            # "X-Auth-Token": settings.API_KEY,
        }
        if requires_access_token:
            access_token = self.request.headers.get("Access-Token")
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            else:
                raise NotAuthenticated("No access token provided in request headers")

        try:
            payload = await self.make_request(
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

        if self.paginated or paginated:
            return payload["content"]
        return payload

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

    async def raise_exception(self, response):
        if response.status_code >= 500:
            raise BoatChargingServerError(response.text)
        if response.status_code == 401:
            raise BoatChargingAuthError()
        if response.status_code == 403:
            raise BoatChargingForbiddenError()
        if response.status_code >= 400:
            raise BoatChargingClientError(response.text)
        return

    def get_location_data(self, item: dict[str, any]) -> dict[str, any]:
        street, number = self.split_address(item["address"])

        location_id = item["id"]
        status = self.location_status_kw_mapping.get(location_id, {}).get(
            "status", "UNKNOWN"
        )
        max_kw = self.location_status_kw_mapping.get(location_id, {}).get("max_kw")

        return {
            "id": item["id"],
            "name": item["name"],
            "address": {
                "city": item["city"],
                "street": street,
                "number": number if number else None,
                "coordinates": {
                    "lat": item["coordinates"]["latitude"],
                    "lon": item["coordinates"]["longitude"],
                },
                "postcode": item["postalCode"],
            },
            "opening_times": {
                "regular_hours": self._convert_regular_hours(
                    item["openingTimes"]["regularHours"]
                ),
                "twentyfourseven": item["openingTimes"]["twentyfourseven"],
                "exceptional_openings": item["openingTimes"]["exceptionalOpenings"],
                "exceptional_closings": item["openingTimes"]["exceptionalClosings"],
            },
            # "available_sockets": item["chargingStationCount"],
            "total_sockets": item["chargingStationCount"],
            "status": status,
            "max_kw": max_kw,
        }

    def _convert_regular_hours(
        self, regular_hours: list[dict[str, str | int]]
    ) -> list[dict[str, any]]:
        """
        The regular hour from the API are in the format:
        {
            "weekday": 1,
            "periodBegin": "08:00",
            "periodEnd": "18:00"
        },
        Convert this to the format expected by the frontend:
        {
            "dayOfWeek": 1,
            "opening": {
              "hours": 8,
              "minutes": 0
            },
            "closing": {
              "hours": 18,
              "minutes": 0
            }
          },
        Where also the number of the day of week is converted from 1-7 (Monday-Sunday) to 0-6 (Sunday-Saturday)
        """
        converted_hours = []
        for entry in regular_hours:
            weekday = entry["weekday"] % 7  # convert 7 to 0. Keep other days the same
            opening_time = entry["periodBegin"]
            closing_time = entry["periodEnd"]

            opening_hours, opening_minutes = map(int, opening_time.split(":"))
            closing_hours, closing_minutes = map(int, closing_time.split(":"))

            converted_hours.append(
                {
                    "dayOfWeek": weekday,
                    "opening": {"hours": opening_hours, "minutes": opening_minutes},
                    "closing": {"hours": closing_hours, "minutes": closing_minutes},
                }
            )
        return converted_hours

    @cache_function(timeout=60, ignore_first_arg=True)
    async def get_location_statuses_and_kw(self) -> dict[str, dict[str, any]]:
        """
        We need to determine the overall status and wattage of each location. To do this we need the data of all charging stations (and their corresponding evses and connectors).
        We loop over each charging station to collect the status and wattage of its connectors, and store this to their corresponding location id.

        Then we can find the max wattage of the connectors and the overall status of the location. We need to take the following steps:
        1. Fetch data of charging stations. Each charging station has a list of evses and each evse has a list of connectors.
        2. Iterate through the connectors per charging station and check the status and wattage of each connector.
        3. Append the status and wattage of each connector to a list of statuses for the location that the charging station belongs to.
        4. Determine the overall status and wattage of the location based on the list of statuses of its connectors.
        """
        charging_stations = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"],
            paginated=True,
        )

        result = {}
        for item in charging_stations:
            location_connectors = []

            for evs in item.get("evses", []):
                for connector in evs.get("connectors", []):
                    state = connector.get("status")
                    wattage = connector.get("maxElectricPower")
                    location_connectors.append((state, wattage))

            status_and_wattage = self.determine_overall_status_and_wattage(
                location_connectors
            )
            result[item["locationId"]] = status_and_wattage

        return result

    def determine_overall_status_and_wattage(
        self, connectors: list[tuple[str, int | None]]
    ) -> dict[str, str | float | None]:
        """
        To determine the overall status and wattage of each location based on the statuses and wattages of its connectors, the logic described below is followed.

        There are three possible status values for a charging station:
        - "OPERATIVE": at least one connector at the location is available
        - "OCCUPIED": all connectors at the location are occupied
        - "INOPERATIVE": no connector is available and at least one connector is out of order

        The wattage of the location is determined by the connector with the highest wattage that is available at the location,
        or if no connector is available, the connector with the highest wattage that is out of order/not available.
        """
        available = [kw for s, kw in connectors if s == "OPERATIVE"]
        occupied = [kw for s, kw in connectors if s == "OCCUPIED"]
        out_of_order = [
            kw for s, kw in connectors if s not in ("OPERATIVE", "OCCUPIED")
        ]

        if available:
            overall_status = "OPERATIVE"
            max_wattage = max_or_none(available)
        elif occupied:
            overall_status = "OCCUPIED"
            max_wattage = max_or_none(occupied)
        else:
            overall_status = "INOPERATIVE"
            max_wattage = max_or_none(out_of_order)

        max_kw = max_wattage / 1000.0 if max_wattage else None
        return {"status": overall_status, "max_kw": max_kw}

    def get_safe_path_param(self, param) -> str:
        """
        Prevent malicious input in the charging station id path parameter.
        Only allow alphanumeric characters, dashes and underscores.
        """
        if not PATH_PARAM_RE.fullmatch(param):
            raise ValidationError("Invalid session id")
        safe_param = urllib_parse_quote(param, safe="")
        return safe_param

    @staticmethod
    def split_address(addr):
        pattern = re.compile(r"^(?P<street>.*?\s)(?P<number>\d.*)$")
        m = pattern.match(addr)
        if not m:
            return addr, ""  # fallback: no number part found
        return m.group("street"), m.group("number")


def boat_charging_openapi_decorator(
    response_serializer_class,
    additional_params=None,
    requires_access_token=True,
    requires_device_id=False,
    paginated=False,
    exceptions=None,
):
    """
    Returns a decorator for DRF schema configuration
    """
    kwargs = {
        "success_response": response_serializer_class,
        "exceptions": [
            BoatChargingClientError,
            BoatChargingServerError,
            BoatChargingMissingAccessToken,
            BoatChargingForbiddenError,
        ],
    }
    if exceptions:
        kwargs["exceptions"].extend(exceptions)

    additional_params = additional_params or []
    if requires_access_token:
        additional_params.append(
            OpenApiParameter(
                name="Access-Token",
                description="EVinity Access Token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
            )
        )
        kwargs["exceptions"].insert(0, BoatChargingMissingAccessToken)
    if requires_device_id:
        additional_params.append(
            OpenApiParameter(
                name=settings.HEADER_DEVICE_ID,
                type=OpenApiTypes.STR,
                location="header",
                required=True,
            )
        )

    if paginated:
        additional_params.append(
            OpenApiParameter(
                name="page",
                required=False,
                type=OpenApiTypes.INT,
                location="query",
            )
        )
        additional_params.append(
            OpenApiParameter(
                name="page_size",
                required=False,
                type=OpenApiTypes.INT,
                location="query",
            )
        )

    return extend_schema_for_api_key(**kwargs, additional_params=additional_params)
