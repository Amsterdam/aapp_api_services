import asyncio
import logging
import re
from typing import Any, Dict

import aiohttp
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.utils.caching_utils import cache_function

logger = logging.getLogger(__name__)


class FetchError(Exception):
    pass


class AddressService:
    def __init__(self) -> None:
        self.url = settings.ADDRESS_SEARCH_URL

    @cache_function(timeout=60 * 60 * 24 * 28)  # Cache the result for 4 weeks
    def batch_get_addresses_by_coordinates(
        self, coords: list[tuple[float, float]]
    ) -> dict[tuple[float, float], Dict[str, Any]]:
        """Synchronous batch address lookup using threads (default, safe for Django views)."""
        logging.info(f"Fetching addresses for {len(coords)} coordinates")
        result = asyncio.run(self.async_batch_get_addresses_by_coordinates(coords))
        return result

    async def async_batch_get_addresses_by_coordinates(
        self, coords: list[tuple[float, float]], max_concurrent_requests: int = 20
    ) -> dict[tuple[float, float], Dict[str, Any]]:
        """
        Asynchronous batch address lookup using aiohttp, for use in async contexts or ETL jobs.
        """
        sem = asyncio.Semaphore(max_concurrent_requests)
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_with_sem(sem, session, lat, lon) for lat, lon in coords
            ]
            results = await asyncio.gather(*tasks)
        return {
            (lat, lon): result
            for (lat, lon), result in zip(coords, results, strict=False)
        }

    async def _fetch_with_sem(self, sem, session, lat, lon):
        async with sem:
            try:
                return await self._async_get_address_by_coordinates(session, lat, lon)
            except Exception as e:
                logger.error(
                    f"Failed to fetch address for coordinates ({lat}, {lon}): {e}"
                )
                return None

    @retry(
        stop=stop_after_attempt(3),  # Retry up to 3 times
        wait=wait_fixed(2),  # Wait 2 seconds between retries
        retry=retry_if_exception_type(FetchError),  # Retry only on custom exceptions
    )
    async def _async_get_address_by_coordinates(
        self, session, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        params = [
            (
                "fl",
                "straatnaam huisnummer huisletter huisnummertoevoeging postcode woonplaatsnaam type nummeraanduiding_id centroide_ll",
            ),
            (
                "qf",
                "exacte_match^1 suggest^0.5 straatnaam^0.6 huisnummer^0.5 huisletter^0.5 huisnummertoevoeging^0.5",
            ),
            ("fq", "bron:BAG"),
            ("bq", "type:weg^1.5"),
            ("bq", "type:adres^1"),
            ("lat", latitude),
            ("lon", longitude),
            ("fq", "type:adres"),
            ("rows", "1"),
        ]
        try:
            async with session.get(
                self.url,
                params=params,
                headers={"Referer": "app.amsterdam.nl"},
                timeout=5,
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Failed to fetch address for coordinates ({latitude}, {longitude}), status code: {response.status}"
                    )
                    raise FetchError(
                        f"Failed to fetch address for coordinates ({latitude}, {longitude}), status code: {response.status}"
                    )
                data = await response.json()
        except aiohttp.ClientError as e:
            logger.info(
                "Failed to fetch data",
                extra={"url": self.url, "params": params},
            )
            raise FetchError(
                f"Failed to fetch address for coordinates ({latitude}, {longitude}): {str(e)}"
            ) from e

        if not data.get("response"):
            logger.error(f"Invalid response: {data}")
            return None

        response_data = (
            self._rename_fields_for_serializer(data=data["response"]["docs"][0])
            if data["response"]["docs"]
            else None
        )
        return response_data

    def construct_params(
        self, latitude: float, longitude: float
    ) -> list[tuple[str, str]]:
        params = [
            (
                "fl",
                "straatnaam huisnummer huisletter huisnummertoevoeging postcode woonplaatsnaam type nummeraanduiding_id centroide_ll",
            ),
            (
                "qf",
                "exacte_match^1 suggest^0.5 straatnaam^0.6 huisnummer^0.5 huisletter^0.5 huisnummertoevoeging^0.5",
            ),
            ("fq", "bron:BAG"),
            ("bq", "type:weg^1.5"),
            ("bq", "type:adres^1"),
            ("lat", latitude),
            ("lon", longitude),
            ("fq", "type:adres"),
            ("rows", "1"),
        ]
        return params

    def _rename_fields_for_serializer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # get lat and long from coordinates
        coordinates = self._get_lat_and_lon_from_coordinates(data["centroide_ll"])
        # change naming of fields
        data["city"] = data["woonplaatsnaam"]
        data["street"] = data["straatnaam"]
        data["lat"] = coordinates[0]
        data["lon"] = coordinates[1]
        data["number"] = data.get("huisnummer", "")
        data["bagId"] = data.get("nummeraanduiding_id", "")

        if data.get("huisletter") is not None and data.get("huisletter") != "":
            data["additionLetter"] = data.get("huisletter")
        if (
            data.get("huisnummertoevoeging") is not None
            and data.get("huisnummertoevoeging") != ""
        ):
            data["additionNumber"] = data.get("huisnummertoevoeging")

        return data

    @staticmethod
    def _get_lat_and_lon_from_coordinates(coordinates: str) -> tuple[float, float]:
        if hasattr(coordinates, "coords"):
            lon, lat = coordinates.coords
            return lat, lon
        m = re.match(r"POINT\(\s*([-0-9.]+)\s+([-0-9.]+)\s*\)", coordinates)
        if not m:
            return None, None
        lon, lat = m.groups()
        return float(lat), float(lon)
