import logging
import re
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta

import requests
from django.conf import settings
from django.utils import timezone
from fpdf import FPDF
from ics import Calendar, Event
from ics.grammar.parse import ContentLine

from waste import constants
from waste.constants import WASTE_TYPES_ORDER
from waste.serializers.waste_guide_serializers import WasteDataSerializer
from waste.services.waste_pdf import (
    WastePDF,
)

montly_pattern = re.compile(r"\d{1}(?:e|de|ste) van de maand")
tz = timezone.get_current_timezone()


class WasteCollectionService:
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

    def create_ics_calendar(self) -> Calendar:
        calendar = Calendar()
        calendar.creator = "-//Amsterdam App//Afvalwijzer kalender//NL"
        calendar.scale = "GREGORIAN"
        calendar.method = "PUBLISH"
        calendar.extra.append(
            ContentLine(
                name="X-WR-CALNAME",
                value="Afvalwijzer kalender",
            )
        )
        for item in self.validated_data:
            if item.get("basisroutetypeCode") not in ["BIJREST", "GROFAFSPR"]:
                dates = self._get_dates_for_waste_item(item)
                for date in dates:
                    calendar = self._add_event_to_calendar(calendar, date, item)

        return calendar

    def create_pdf_calendar_dates(self) -> dict[date, list[str]]:
        waste_collection_by_date = {}
        for item in self.validated_data:
            if item.get("basisroutetypeCode") not in ["BIJREST", "GROFAFSPR"]:
                dates = self._get_dates_for_waste_item(item)
                for date in dates:
                    waste_collection_by_date.setdefault(date, []).append(
                        item.get("label")
                    )

        return waste_collection_by_date

    def _add_event_to_calendar(self, calendar: Calendar, date: date, item: dict):
        event = self._create_ics_event(date, item)
        calendar.events.add(event)
        return calendar

    def _create_ics_event(self, date: date, item: dict) -> Event:
        event = Event()

        # set unique id and name
        event.uid = f"{item.get('label', '').replace(',', '').replace(' ', '')}-{date.isoformat()}@app.amsterdam.nl"
        event.name = f"Ophaaldag {item.get('label', '').lower()}"

        # set date of event
        event.begin = date
        event.make_all_day()

        # set created and dtstamp to now (required for iCalendar)
        event.created = timezone.now()
        event.dtstamp = timezone.now()

        # set description
        event.description = ""
        if item.get("curb_rules_from") and item.get("curb_rules_to"):
            event.description += f"Buiten zetten: {item.get('curb_rules_from', '')} {item.get('curb_rules_to', '')}"

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
                        "info_link": self.waste_links.get(code),
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

    def get_pdf_calendar(self) -> FPDF:
        # get all necessary data
        waste_collection_by_date = self.create_pdf_calendar_dates()
        days = self._get_dates()
        months = self.group_days_by_month(days)

        # initialize pdf and get settings
        pdf = WastePDF(address=self._generate_address_string())
        pdf.add_page()
        pdf.add_title()

        # draw months
        for (year, month), month_days in months.items():
            needed_height = pdf.estimate_month_height(year, month, month_days)
            if pdf.remaining_page_height() < needed_height:
                pdf.add_page()
            pdf.draw_pdf_month(year, month, month_days, waste_collection_by_date)

        return pdf

    def _generate_address_string(self) -> str:
        if not self.validated_data or len(self.validated_data) == 0:
            return ""
        first_item = self.validated_data[0]
        street_name = first_item.get("street_name", "")
        house_number = first_item.get("house_number", "")
        house_letter = first_item.get("house_letter", "")
        house_number_addition = first_item.get("house_number_addition", "")
        postal_code = first_item.get("postal_code", "")
        city_name = first_item.get("city_name", "")

        address_parts = [street_name, house_number]
        if house_letter:
            address_parts.append(house_letter)
        if house_number_addition:
            address_parts.append(house_number_addition)
        address = " ".join(address_parts)
        if postal_code:
            address += f", {postal_code}"
        if city_name:
            address += f" {city_name}"

        return address.strip()

    @staticmethod
    def group_days_by_month(days: list[date]) -> OrderedDict:
        months = OrderedDict()
        for d in days:
            key = (d.year, d.month)
            months.setdefault(key, []).append(d)
        return months
