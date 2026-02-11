import re
from datetime import date, datetime, timedelta

import requests
from django.conf import settings

from waste.interpret_frequencies import interpret_frequencies
from waste.serializers.waste_guide_serializers import WasteDataSerializer


class WasteCollectionAbstractService:
    def __init__(self, bag_nummeraanduiding_id: str):
        self.bag_nummeraanduiding_id = bag_nummeraanduiding_id
        self.validated_data = []
        self.all_dates = self._get_dates()
        self.waste_links = {
            "Glas": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/glas-potten-flessen-en-ander-glas/",
            "Papier": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/papier-en-karton/",
            "GFT": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/groente-fruit-en-tuinafval-gft/",
            "Rest": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/restafval/",
            "GA": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/grofvuil/",
            "Textiel": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/kleding-textiel-en-schoenen/",
        }

    @staticmethod
    def _get_dates() -> list[date]:
        now = datetime.now()
        end_date = now + timedelta(days=settings.CALENDAR_LENGTH - 1)
        dates = [(now + timedelta(n)).date() for n in range((end_date - now).days + 1)]
        return dates

    def get_validated_data(self):
        url = settings.WASTE_GUIDE_URL
        api_key = settings.WASTE_GUIDE_API_KEY
        headers = None
        if settings.ENVIRONMENT_SLUG in ["a", "p"]:
            headers = {"X-Api-Key": api_key}
        resp = requests.get(
            url,
            params={"bagNummeraanduidingId": self.bag_nummeraanduiding_id},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json().get("_embedded", {}).get("afvalwijzer", [])
        serializer = WasteDataSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        data = [d for d in serializer.validated_data if d.get("code")]
        self.validated_data = data

    def get_dates_for_waste_item(self, item) -> list[date]:
        ophaaldagen_list, dates = self.filter_ophaaldagen(ophaaldagen=item.get("days"))
        dates = interpret_frequencies(dates, item, ophaaldagen_list)
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
