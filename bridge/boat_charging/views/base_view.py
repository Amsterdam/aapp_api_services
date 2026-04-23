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
    async def make_request(self, *, body_data, endpoint, headers, method, query_params):
        response = await client.request(
            method=method,
            url=endpoint,
            params=query_params,
            json=body_data,
            headers=headers,
        )
        if response.is_success:
            return response.json()
        return await self.raise_exception(response)

    async def raise_exception(self, response):
        if response.status_code >= 500:
            raise BoatChargingServerError()
        if response.status_code == 401:
            raise BoatChargingAuthError()
        if response.status_code >= 400:
            raise BoatChargingClientError()
        return

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
                "regular_hours": item["openingTimes"]["regularHours"],
                "twentyfourseven": item["openingTimes"]["twentyfourseven"],
                "exceptional_openings": item["openingTimes"]["exceptionalOpenings"],
                "exceptional_closings": item["openingTimes"]["exceptionalClosings"],
            },
            # "available_sockets": item["chargingStationCount"],
            "total_sockets": item["chargingStationCount"],
        }

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
