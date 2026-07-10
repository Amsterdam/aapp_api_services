import logging
from datetime import datetime

import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.views import APIView

from contact.serializers.pride_event_serializers import PrideEventResponseSerializer
from contact.services.pride_map import PrideMapService
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 10), name="dispatch")  # Cache 10 mins
class PrideEventsView(APIView, PrideMapService):
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
        date_time_properties = self._get_start_end_date_and_time_properties_from_meta(
            props
        )

        event_type, time = None, None
        for meta in props["meta"]:
            if meta["key"] == "type":
                event_type = meta["value"]
                if event_type == "BOTENPARADE":
                    event_type = "Canal Parade"
            elif meta["key"] == "tijd":
                time = meta["value"]

        # Clean some data noise
        title = props["title"].replace("(de datum op de website is ander)", "").strip()
        description = props.get("description")
        if description == "???":
            description = None
        return {
            "id": props["id"],
            "title": title,
            "description": description,
            "address": {
                "street": props.get("street", "onbekend"),
                "city": props["city"],
                "coordinates": {
                    "lat": coordinates[1],
                    "lon": coordinates[0],
                },
            },
            "website": self._get_website(props),
            "date_start": date_time_properties.get("start_date"),
            "date_end": date_time_properties.get("end_date"),
            "type": event_type,
            "time": time,
        }
