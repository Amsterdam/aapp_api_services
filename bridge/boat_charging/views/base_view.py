import logging

import httpx
from adrf.generics import GenericAPIView
from rest_framework.exceptions import NotAuthenticated
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.boat_charging.client import client
from bridge.boat_charging.exceptions import (
    BoatChargingClientError,
    BoatChargingServerError,
)

logger = logging.getLogger(__name__)


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
    ):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",  # necessary to get through WAF
            # "X-Auth-Token": settings.API_KEY,
        }
        if requires_access_token:
            access_token = self.request.headers.get("access_token")
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

        if self.paginated:
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
        if response.status_code >= 400:
            raise BoatChargingClientError()
        return

    def get_location_data(self, item) -> dict:
        return {
            "id": item["id"],
            "name": item["name"],
            "address": {
                "city": item["city"],
                "street": item["address"],  # The street contains the house number!
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
