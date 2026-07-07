import logging
import re
from datetime import datetime

import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.views import APIView

from contact.serializers.pride_event_serializers import PrideEventResponseSerializer
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 10), name="dispatch")  # Cache 10 mins
class PrideEventsView(APIView):
    @extend_schema_for_api_key(
        success_response=PrideEventResponseSerializer(many=True),
    )
    def get(self, request):
        response = requests.get(settings.PRIDE_EVENT_URL)
        response.raise_for_status()
        data = response.json()
        formatted_data = [self._format_data(feature) for feature in data["features"]]

        serializer = PrideEventResponseSerializer(data=formatted_data, many=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Sort and filter data
        sorted_data = sorted(
            validated_data,
            key=lambda x: (
                x["datum_start"] or datetime(year=3000, month=1, day=1).date()
            ),
        )
        filtered_data = [
            d
            for d in sorted_data
            if d["datum_end"]
            or datetime(year=3000, month=1, day=1).date() > datetime.today().date()
        ]
        return Response(filtered_data)

    def _format_data(self, feature):
        coordinates = feature["geometry"]["coordinates"]
        props = feature["properties"]

        event_type, datum_start, datum_eind, tijd = None, None, None, None
        for meta in props["meta"]:
            if meta["key"] == "type":
                event_type = meta["value"]
            elif meta["key"] == "datum-start":
                datum_start = meta["value"]
            elif meta["key"] == "datum-eind":
                datum_eind = meta["value"]
            elif meta["key"] == "tijd":
                tijd = meta["value"]

        return {
            "id": props["id"],
            "title": props["title"],
            "description": props.get("description"),
            "address": {
                "street": props.get("street", "onbekend"),
                "city": props["city"],
                "coordinates": {
                    "lat": coordinates[0],
                    "lon": coordinates[0],
                },
            },
            "website": props.get("website"),
            "type": event_type,
            "datum_start": self._convert_date_string_to_iso_format(datum_start),
            "datum_end": self._convert_date_string_to_iso_format(datum_eind),
            "tijd": tijd,
        }

    def _convert_date_string_to_iso_format(self, date_string: str | None) -> str | None:
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
        match = re.search(r"\d{1,2}-[a-zA-Z]{3}", date_string)
        if match:
            date_string = match.group(0)
            date_string += f"-{datetime.now().year}"
            try:
                date_obj = datetime.strptime(date_string, "%d-%b-%Y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                logger.warning(f"Could not convert date string: {date_string}")
