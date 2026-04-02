import logging
import re
from datetime import date, timedelta
from typing import Literal

import requests
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.utils.caching_utils import cache_function
from waste.exceptions import WasteGuideException
from waste.interpret_frequencies import interpret_frequencies
from waste.models import WasteCollectionException
from waste.serializers.waste_guide_serializers import WasteDataSerializer

logger = logging.getLogger(__name__)


class WasteCollectionAbstractService:
    def __init__(self):
        self.all_dates = self._get_dates()
        self.waste_links = {
            "Glas": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/glas-potten-flessen-en-ander-glas/",
            "Papier": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/papier-en-karton/",
            "GFT": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/groente-fruit-en-tuinafval-gft/",
            "Rest": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/restafval/",
            "GA": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/grofvuil/",
            "Textiel": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/kleding-textiel-en-schoenen/",
        }

    def _get_dates(self) -> list[date]:
        now = date.today()
        dates = [now + timedelta(days=n) for n in range(settings.CALENDAR_LENGTH)]
        return dates

    def get_validated_data_for_bag_id(self, bag_id):
        params = {"bagNummeraanduidingId": bag_id}
        url = settings.WASTE_GUIDE_URL
        data, _ = self.get_validated_data(url=url, params=params)
        return data

    def get_validated_data(self, *, url, params):
        api_key = settings.WASTE_GUIDE_API_KEY
        headers = None
        if settings.ENVIRONMENT_SLUG in ["a", "p"]:
            headers = {"X-Api-Key": api_key}
        try:
            response_json = self.make_request(
                method="GET",
                url=url,
                headers=headers,
                params=params,
            )
            data = response_json.get("_embedded", {}).get("afvalwijzer", [])
        except requests.RequestException as e:
            logger.error(f"Error fetching waste data: {e}")
            raise WasteGuideException() from e

        serializer = WasteDataSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        data = [d for d in serializer.validated_data if d.get("code")]
        next_link = response_json.get("_links", {}).get("next", {}).get("href")
        return data, next_link

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def make_request(
        self,
        method: Literal["GET", "POST"],
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_dates_for_waste_item(self, item) -> list[date]:
        ophaaldagen_list, dates = self.filter_ophaaldagen(ophaaldagen=item.get("days"))
        frequency = item.get("frequency")
        note = item.get("note")
        dates = interpret_frequencies(
            dates=dates,
            frequency=frequency,
            note=note,
            ophaaldagen_list=ophaaldagen_list,
        )
        dates = self._filter_dates_on_exceptions(dates=dates, item=item)
        return dates

    def filter_ophaaldagen(self, ophaaldagen):
        ophaaldagen_list = self._interpret_ophaaldagen(ophaaldagen)
        dates = [date for date in self.all_dates if date.weekday() in ophaaldagen_list]
        return ophaaldagen_list, dates

    @staticmethod
    def _interpret_ophaaldagen(ophaaldagen: str) -> list[int]:
        days_of_week = {
            "maandag": 0,
            "dinsdag": 1,
            "woensdag": 2,
            "donderdag": 3,
            "vrijdag": 4,
            "zaterdag": 5,
            "zondag": 6,
        }
        if not ophaaldagen:
            return []
        ophaaldagen_list = re.split(r",| en ", ophaaldagen)
        ophaaldagen_mapped = [days_of_week[d.strip()] for d in ophaaldagen_list]
        return ophaaldagen_mapped

    def _filter_dates_on_exceptions(
        self, dates: list[date], item: dict[str, str]
    ) -> list[date]:
        future_dates = self._get_future_dates()
        dates_overlap = set(dates) & set(future_dates)
        if not dates_overlap:
            return dates

        item_route = item.get("route_name")
        for affected_date in dates_overlap:
            affected_routes = self._get_affected_routes_for_date(affected_date)
            if item_route in affected_routes:
                dates.remove(affected_date)

        return dates

    @staticmethod
    @cache_function(timeout=60 * 60)  # cache one hour
    def _get_future_dates() -> list[date]:
        return list(
            WasteCollectionException.objects.filter(date__gte=date.today()).values_list(
                "date", flat=True
            )
        )

    @staticmethod
    @cache_function(timeout=60 * 60)  # Cache for one hour
    def _get_affected_routes_for_date(date: date) -> list[str]:
        # cache this function because when sending notifications it will be called multiple times for the same date
        return list(
            WasteCollectionException.objects.filter(date=date).values_list(
                "affected_routes__name", flat=True
            )
        )
