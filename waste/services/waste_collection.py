import re
from collections import defaultdict
from datetime import datetime, timedelta

import requests
from django.conf import settings

from waste.serializers.waste_guide_serializers import WasteDataSerializer


class WasteCollectionService:
    def __init__(self, bag_nummeraanduiding_id):
        self.bag_nummeraanduiding_id = bag_nummeraanduiding_id
        self.validated_data = []
        self.all_dates = self._get_dates()

    def get_validated_data(self):
        url = settings.WASTE_GUIDE_URL
        api_key = settings.WASTE_GUIDE_API_KEY
        resp = requests.get(
            url,
            params={"bagNummeraanduidingId": self.bag_nummeraanduiding_id},
            headers={"X-Api-Key": api_key},
        )
        resp.raise_for_status()
        data = resp.json().get("_embedded", {}).get("afvalwijzer", [])
        serializer = WasteDataSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        self.validated_data = serializer.validated_data

    def create_calendar(self):
        calendar = []
        for item in self.validated_data:
            dates = self.filter_ophaaldagen(
                ophaaldagen=item.get("afvalwijzerOphaaldagen")
            )
            frequency = item.get("afvalwijzerAfvalkalenderFrequentie") or ""
            if "oneven" in frequency:
                dates = self.filter_even_oneven(dates, even=False)
            elif "even" in frequency:
                dates = self.filter_even_oneven(dates, even=True)
            elif "/" in frequency:
                dates = self.filter_specific_dates(dates, frequency)

            calendar += [
                {
                    "date": date,
                    "label": item.get("afvalwijzerFractieNaam"),
                    "type": item.get("afvalwijzerFractieCode"),
                    "curb_rules_from": item.get("afvalwijzerBuitenzettenVanaf"),
                    "curb_rules_to": item.get("afvalwijzerBuitenzettenTot"),
                    "note": item.get("afvalwijzerAfvalkalenderMelding"),
                }
                for date in dates
            ]
        # sort calendar items by date
        calendar.sort(key=lambda x: x["date"])
        return calendar

    def filter_ophaaldagen(self, ophaaldagen):
        ophaaldagen_list = self._interpret_ophaaldagen(ophaaldagen)
        all_dates = self._get_dates()
        dates = [date for date in all_dates if date.weekday() in ophaaldagen_list]
        return dates

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

    def filter_even_oneven(self, dates, even):
        filtered_dates = [d for d in dates if d.isocalendar()[1] % 2 != even]
        return filtered_dates

    def filter_specific_dates(self, dates, frequency):
        parts = re.findall(r"\d{1,2}-\d{1,2}-\d{2}", frequency)
        specific_dates = []
        for part in parts:
            date = datetime.strptime(part.strip(), "%d-%m-%y").date()
            specific_dates.append(date)
        return [d for d in dates if d in specific_dates]

    def get_next_dates(self, calendar):
        dates = defaultdict(list)
        for item in calendar:
            type = item.get("type")
            dates[type].append(item["date"])

        next_dates = {type: None for type in settings.WASTE_TYPES}
        for type in next_dates:
            next_dates[type] = min(dates[type]) if dates[type] else None

        return next_dates

    def get_waste_types(self, next_dates):
        waste_types = []
        for item in self.validated_data:
            type = item.get("afvalwijzerFractieCode")
            waste_types.append(
                {
                    "label": item.get("afvalwijzerFractieNaam"),
                    "type": type,
                    "curb_rules_from": item.get("afvalwijzerBuitenzettenVanaf"),
                    "curb_rules_to": item.get("afvalwijzerBuitenzettenTot"),
                    "remark": item.get("afvalwijzerAfvalkalenderOpmerking"),
                    "note": item.get("afvalwijzerAfvalkalenderMelding"),
                    "instruction": item.get("afvalwijzerInstructie2"),
                    "next_date": next_dates.get(type),
                }
            )
        return waste_types

    def _get_dates(self):
        now = datetime.now()
        end_date = now + timedelta(days=settings.CALENDAR_LENGTH - 1)
        dates = [(now + timedelta(n)).date() for n in range((end_date - now).days + 1)]
        return dates
