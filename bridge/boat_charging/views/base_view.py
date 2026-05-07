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
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)
PATH_PARAM_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class BaseView(GenericAPIView):
    serializer_class = None
    response_serializer_class = None
    requires_access_token = False
    paginated = False

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

    def get_location_feature_data(self, item) -> dict:
        item_dict = self.get_location_data(item)
        return {
            "type": "Feature",
            "properties": item_dict,
            "geometry": {
                "type": "Point",
                "coordinates": [
                    item["coordinates"]["longitude"],
                    item["coordinates"]["latitude"],
                ],
            },
        }

    def get_location_data(self, item) -> dict:
        street, number = self.split_address(item["address"])

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
        }

    def _convert_regular_hours(self, regular_hours: list) -> list:
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
