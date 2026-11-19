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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.location_status_kw_mapping = None

    async def api_call(
        self,
        method,
        endpoint,
        body_data=None,
        query_params=None,
        paginated=False,
        timeout=None,
    ):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",  # necessary to get through WAF
            # "X-Auth-Token": settings.API_KEY,
        }
        access_token = self.request.headers.get("Access-Token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        elif self.requires_access_token:
            raise NotAuthenticated("No access token provided in request headers")

        try:
            payload = await self.make_request(
                method=method,
                endpoint=endpoint,
                headers=headers,
                query_params=query_params,
                body_data=body_data,
                timeout=timeout,
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
        timeout=None,
    ):
        assert not (body_data and data), (
            "Either body_data or data must be provided, not both"
        )
        request_kwargs = {
            "method": method,
            "url": endpoint,
            "params": query_params,
            "json": body_data,
            "data": data,
            "headers": headers,
            "auth": auth,
        }
        if timeout is not None:
            request_kwargs["timeout"] = timeout

        response = await client.request(
            **request_kwargs,
        )
        if response.is_success:
            if response.status_code == 204 or not response.content:
                return {}
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
            logger.warning(f"Client error: {response.status_code} - {response.text}")
            raise BoatChargingClientError(response.text)
        return

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
            return addr.strip(), ""  # fallback: no number part found
        return m.group("street").strip(), m.group("number").strip()


def boat_charging_openapi_decorator(
    response_serializer_class,
    success_status_code=200,
    additional_params=None,
    accepts_access_token=True,
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
            BoatChargingForbiddenError,
        ],
    }
    if exceptions:
        kwargs["exceptions"].extend(exceptions)

    additional_params = additional_params or []
    if accepts_access_token:
        additional_params.append(
            OpenApiParameter(
                name="Access-Token",
                description="EVinity Access Token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=requires_access_token,
            )
        )
        if requires_access_token:
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
    return extend_schema_for_api_key(
        **kwargs,
        success_status_code=success_status_code,
        additional_params=additional_params,
    )
