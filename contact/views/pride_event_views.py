import logging
import re
from datetime import date, datetime, timedelta

import requests
from babel.dates import get_month_names
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.views import APIView

from contact.serializers.pride_event_serializers import (
    PrideDateEventResponseSerializer,
    PrideEventResponseSerializer,
)
from core.utils.caching_utils import cache_function
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 10), name="dispatch")  # Cache 10 mins
class PrideEventsView(APIView):
    @extend_schema_for_api_key(
        success_response=PrideEventResponseSerializer(many=True),
    )
    def get(self, request):
        response = requests.get(settings.PRIDE_EVENT_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        formatted_data = [self._format_data(feature) for feature in data["features"]]

        serializer = PrideEventResponseSerializer(data=formatted_data, many=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Sort and filter data
        sorted_data = sorted(
            validated_data,
            key=lambda x: x["date_start"] or datetime(year=3000, month=1, day=1).date(),
        )
        filtered_data = [
            d
            for d in sorted_data
            if d["date_end"]
            or datetime(year=3000, month=1, day=1).date() > datetime.today().date()
        ]
        return Response(filtered_data)

    def _format_data(self, feature):
        coordinates = feature["geometry"]["coordinates"]
        props = feature["properties"]

        event_type, date_start, date_end, time = None, None, None, None
        for meta in props["meta"]:
            if meta["key"] == "type":
                event_type = meta["value"]
            elif meta["key"] == "datum-start":
                date_start = meta["value"]
            elif meta["key"] == "datum-eind":
                date_end = meta["value"]
            elif meta["key"] == "tijd":
                time = meta["value"]

        return {
            "id": props["id"],
            "title": props["title"],
            "description": props.get("description"),
            "address": {
                "street": props.get("street", "onbekend"),
                "city": props["city"],
                "coordinates": {
                    "lat": coordinates[1],
                    "lon": coordinates[0],
                },
            },
            "website": props.get("website"),
            "type": event_type,
            "date_start": _convert_date_string_to_iso_format(date_start),
            "date_end": _convert_date_string_to_iso_format(date_end),
            "time": time,
        }


# @method_decorator(cache_page(60 * 10), name="dispatch")  # Cache 10 mins
class PrideDateEventsView(APIView):
    @extend_schema_for_api_key(
        success_response=PrideDateEventResponseSerializer(many=True),
    )
    def get(self, request):
        response = requests.get(settings.PRIDE_EVENT_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        event_types = set()
        formatted_data = []
        for feature in data["features"]:
            formatting_result = self._format_data(feature)
            event_type = formatting_result[0]["type"] if formatting_result else None
            event_types.add(event_type)
            if formatting_result:
                formatted_data.extend(formatting_result)

        # Sort and filter data
        sorted_data = sorted(
            formatted_data,
            key=lambda x: (
                x.get("date_start") or datetime(year=3000, month=1, day=1).date()
            ),
        )
        filtered_data = [
            d
            for d in sorted_data
            if d.get("date_end")
            or datetime(year=3000, month=1, day=1).date() > datetime.today().date()
        ]

        # now change the shape of the data. We now have a list of events, but we want to group them by date. So we will create a dictionary where the key is the date and the value is a list of events for that date.
        grouped_data = {}
        for event in filtered_data:
            event_date = event.get("date")
            if not event_date:
                logger.warning(f"Event with id {event['id']} has no date. Skipping.")
                continue
            if event_date not in grouped_data:
                grouped_data[event_date] = []
            grouped_data[event_date].append(event)

        # then rework the shape again to have a list of dictionaries where each dictionary has a date and a list of events for that date.
        grouped_list_data = [
            {"date": date, "events": events} for date, events in grouped_data.items()
        ]

        serializer = PrideDateEventResponseSerializer(data=grouped_list_data, many=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        return Response(validated_data)

    def _format_data(self, feature) -> list[dict]:
        coordinates = feature["geometry"]["coordinates"]
        props = feature["properties"]

        event_type, date_start, date_end, time = None, None, None, None
        for meta in props["meta"]:
            if meta["key"] == "type":
                event_type = meta["value"]
            elif meta["key"] == "datum-start":
                date_start = meta["value"]
            elif meta["key"] == "datum-eind":
                date_end = meta["value"]
            elif meta["key"] == "tijd":
                time = meta["value"]

        if date_start and date_end:
            # check if they are equal to each other, if so, set date to date_start
            if _convert_date_string_to_iso_format(
                date_start
            ) == _convert_date_string_to_iso_format(date_end):
                event_date = _convert_date_string_to_iso_format(date_start)
                return [
                    self._format_response(
                        props,
                        coordinates,
                        event_type,
                        event_date,
                        date_start,
                        date_end,
                        time,
                    )
                ]

            else:
                # if they are not equal we want to return a response for each date, so we will return a list of responses
                event_date_start = _convert_date_string_to_iso_format(date_start)
                event_date_end = _convert_date_string_to_iso_format(date_end)
                # first calculate each date between the start and end date, and return a response for each date
                start_date_obj = datetime.strptime(event_date_start, "%Y-%m-%d")
                end_date_obj = datetime.strptime(event_date_end, "%Y-%m-%d")
                date_list = [
                    (start_date_obj + timedelta(days=x)).strftime("%Y-%m-%d")
                    for x in range((end_date_obj - start_date_obj).days + 1)
                ]
                return [
                    self._format_response(
                        props, coordinates, event_type, x, date_start, date_end, time
                    )
                    for x in date_list[1:]
                ]

        if date_start:
            event_date = _convert_date_string_to_iso_format(date_start)
            return [
                self._format_response(
                    props,
                    coordinates,
                    event_type,
                    event_date,
                    date_start,
                    date_end,
                    time,
                )
            ]

        if date_end:
            event_date = _convert_date_string_to_iso_format(date_end)
            return [
                self._format_response(
                    props,
                    coordinates,
                    event_type,
                    event_date,
                    date_start,
                    date_end,
                    time,
                )
            ]

        else:
            logger.warning(
                f"Feature with id {props['id']} has no start or end date. Skipping."
            )
            return []

    def _format_response(
        self, props, coordinates, event_type, event_date, date_start, date_end, time
    ):
        return {
            "id": props["id"],
            "title": props["title"],
            "description": props.get("description"),
            "address": {
                "street": props.get("street", "onbekend"),
                "city": props["city"],
                "coordinates": {
                    "lat": coordinates[1],
                    "lon": coordinates[0],
                },
            },
            "website": props.get("website"),
            "type": event_type,
            "date": event_date,
            "date_start": _convert_date_string_to_iso_format(date_start),
            "date_end": _convert_date_string_to_iso_format(date_end),
            "time": time,
        }


@cache_function(timeout=60 * 60 * 24)  # Cache for 24 hours
def _convert_date_string_to_iso_format(date_string: str | None) -> str | None:
    """
    Converts a date string to 'YYYY-MM-DD'.

    Expected input formats:
    - 8-jul -> important!! current year is assumed, so if the current year is 2026, the output will be 2026-07-08
    - YYYY-MM-DD
    - YYYY-MM-DDgarbage
    If the input is not in the expected format, returns None and log other format.
    """
    if not date_string:
        return None

    # use regex to check if the string contains a date in the format 'YYYY-MM-DD', if so, return it
    match = re.search(r"\d{4}-\d{2}-\d{2}", date_string)
    if match:
        return match.group(0)

    # check if the string contains a date in the format 'DD-MMM', if so, convert it to 'YYYY-MM-DD' using the current year
    # for example, 8-jul -> 2026-07-08
    match = re.search(r"\d{1,2}-[a-zA-Z.]{3,}", date_string)
    if match:
        short_date = match.group(0)
        day_str, month_name = short_date.split("-", maxsplit=1)
        month_number = _get_month_number_from_name(month_name)
        current_year = datetime.now().year

        try:
            date_obj = date(
                year=current_year,
                month=month_number,
                day=int(day_str),
            )
            if date_obj < date.today():
                date_obj = date(
                    year=current_year + 1,
                    month=month_number,
                    day=int(day_str),
                )
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(
                f"Could not convert date string: {short_date}-{current_year}"
            )
            return None


@cache_function(timeout=60 * 60 * 24)  # Cache for 24 hours
def _get_month_number_from_name(month_name: str) -> int | None:
    normalized_month = month_name.strip().lower().rstrip(".")

    month_names = get_month_names(width="abbreviated", locale="nl_NL")
    for month_number, localized_month_name in month_names.items():
        if not localized_month_name:
            continue
        if localized_month_name.strip().lower().rstrip(".") == normalized_month:
            return month_number
    return None
