import logging
import re
from collections import defaultdict
from datetime import date, datetime, timedelta

import requests
from django.conf import settings
from ics import Calendar, Event

from waste import constants
from waste.constants import WASTE_TYPES_ORDER
from waste.serializers.waste_guide_serializers import WasteDataSerializer

montly_pattern = re.compile(r"\d{1}(?:e|de|ste) van de maand")


class WasteCollectionService:
    def __init__(self, bag_nummeraanduiding_id: str):
        self.bag_nummeraanduiding_id = bag_nummeraanduiding_id
        self.validated_data = []
        self.all_dates = self._get_dates()

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

    def _get_dates_for_waste_item(self, item) -> list[date]:
        ophaaldagen_list, dates = self.filter_ophaaldagen(ophaaldagen=item.get("days"))
        frequency = item.get("frequency") or ""
        if frequency == "":
            pass  # no filtering needed
        elif "oneven" in frequency:
            dates = self.filter_even_oneven(dates, even=False)
        elif "even" in frequency:
            dates = self.filter_even_oneven(dates, even=True)
        elif "/" in frequency:
            dates = self.filter_specific_dates(dates, frequency)
        elif montly_pattern.match(frequency) is not None:
            dates = self.filter_nth_weekday_dates(
                dates, weekday=ophaaldagen_list[0], frequency=frequency
            )
        else:
            logging.error(
                f"Unknown frequency pattern '{frequency}' for waste type {item.get('code')}"
            )
            dates = []

        return dates

    def create_calendar(self):
        calendar = []
        for item in self.validated_data:
            if item.get("basisroutetypeCode") not in ["BIJREST", "GROFAFSPR"]:
                dates = self._get_dates_for_waste_item(item)
                calendar += [
                    {
                        "date": date,
                        **{
                            k: item.get(k)
                            for k in [
                                "label",
                                "code",
                                "curb_rules_from",
                                "curb_rules_to",
                                "alert",
                            ]
                        },
                    }
                    for date in dates
                ]
        # sort calendar items by date
        calendar.sort(key=lambda x: x["date"])
        return calendar

    def create_ics_calendar(self):
        calendar = Calendar()
        for item in self.validated_data:
            if item.get("basisroutetypeCode") not in ["BIJREST", "GROFAFSPR"]:
                dates = self._get_dates_for_waste_item(item)
                for date in dates:
                    calendar = self._add_event_to_calendar(calendar, date, item)

        return calendar

    def _add_event_to_calendar(self, calendar: Calendar, date: date, item: dict):
        event = self._create_ics_event(date, item)
        calendar.events.add(event)
        return calendar

    def _create_ics_event(self, date: date, item: dict) -> Event:
        event = Event(
            uid=f"{item.get('label')}-{date.isoformat()}@app.amsterdam.nl",
            name=item.get("label", "Afval ophalen"),
            begin=datetime.combine(date, datetime.min.time()),
            description=f"Afval ophalen voor type: {item.get('label')}",
        )
        event.make_all_day()
        if item.get("curb_rules_from") and item.get("curb_rules_to"):
            event.description += f"\nAfval aanbieden: {item.get('curb_rules_from', '')} {item.get('curb_rules_to', '')}"
        if item.get("alert"):
            event.description += f"\nAlert: {item.get('alert')}"
        return event

    def filter_ophaaldagen(self, ophaaldagen):
        ophaaldagen_list = self._interpret_ophaaldagen(ophaaldagen)
        all_dates = self._get_dates()
        dates = [date for date in all_dates if date.weekday() in ophaaldagen_list]
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

    def filter_even_oneven(self, dates: list[date], even: bool) -> list[date]:
        filtered_dates = [d for d in dates if d.isocalendar()[1] % 2 != even]
        return filtered_dates

    def filter_nth_weekday_dates(
        self, dates: list[date], weekday: int, frequency: str
    ) -> list[date]:
        # get nth from frequency string
        n = int(frequency[0])
        filtered_dates = [
            d
            for d in dates
            if self.determine_nth_weekday_date(dt=d, weekday=weekday, n=n)
        ]
        return filtered_dates

    def determine_nth_weekday_date(self, dt: date, weekday: int, n: int) -> bool:
        """
        Return True if date `dt` is the `n`-th occurrence of `weekday` in its month.

        Making use of the difference in days between date and first occurence
        # For example:
        #   n=1 → diff_days in [0, 6]
        #   n=2 → diff_days in [7, 13]
        #   n=3 → diff_days in [14, 20], etc.

        weekday: Monday=0, ..., Sunday=7
        n: occurrence number (1=1st, 2=2nd, 3=3rd, ...)
        """
        # First day of the month
        first = dt.replace(day=1)

        # First occurrence of target weekday in the month
        days_until_target = (weekday - first.weekday()) % 7
        first_occurrence = first + timedelta(days=days_until_target)

        # Compute which occurrence dt is
        diff_days = (dt - first_occurrence).days

        return 7 * (n - 1) <= diff_days <= 7 * n - 1

    def filter_specific_dates(self, dates: list[date], frequency: str) -> list[date]:
        # get parts without a year
        parts = re.findall(r"\d{1,2}-\d{1,2}", frequency)
        specific_dates = []
        today = datetime.today()
        year = today.year
        for part in parts:
            day, month = map(int, part.split("-"))

            # Create a mock date for the current year
            year_date = datetime(year, month, day)

            # If this date has passed already, put it in next year
            if year_date < today:
                year_date = year_date.replace(year=year + 1)

            specific_dates.append(year_date.date())

        # get parts with a year
        parts = re.findall(r"\d{1,2}-\d{1,2}-\d{2}", frequency)
        for part in parts:
            date = datetime.strptime(part.strip(), "%d-%m-%y").date()
            specific_dates.append(date)
        return [d for d in dates if d in specific_dates]

    def get_next_dates(self, calendar):
        dates = defaultdict(list)
        for item in calendar:
            code = item.get("code")
            dates[code].append(item["date"])

        next_dates = {code: None for code in WASTE_TYPES_ORDER}
        for code in next_dates:
            next_dates[code] = min(dates[code]) if dates[code] else None

        return next_dates

    def get_waste_types(self, next_dates):
        waste_types = []
        for item in self.validated_data:
            code = item.get("code")
            if code in constants.WASTE_TYPES_ORDER:
                waste_types.append(
                    {
                        **{
                            k: item.get(k)
                            for k in [
                                "label",
                                "code",
                                "curb_rules",
                                "alert",
                                "note",
                                "days_array",
                                "how",
                                "where",
                                "button_text",
                                "url",
                                "frequency",
                                "is_collection_by_appointment",
                            ]
                        },
                        "next_date": next_dates.get(code),
                    }
                )
        waste_types.sort(
            key=lambda x: (
                WASTE_TYPES_ORDER.index(x["code"])
                if x["code"] in WASTE_TYPES_ORDER
                else 999
            )
        )
        return waste_types

    def get_is_residential(self):
        if self.validated_data and len(self.validated_data) > 0:
            return self.validated_data[0].get("is_residential")
        return True

    def get_is_collection_by_appointment(self):
        for item in self.validated_data:
            if item.get("code") == "Rest":
                return item.get("is_collection_by_appointment")
        return False

    def _get_dates(self) -> list[date]:
        now = datetime.now()
        end_date = now + timedelta(days=settings.CALENDAR_LENGTH - 1)
        dates = [(now + timedelta(n)).date() for n in range((end_date - now).days + 1)]
        return dates
