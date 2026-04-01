from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.location import LocationResponseSerializer
from bridge.boat_charging.views.base_view import BaseView
from core.services.internal_http_client import InternalServiceSession
from core.utils.openapi_utils import extend_schema_for_api_key

internal_client = InternalServiceSession()


@extend_schema_for_api_key(success_response=LocationResponseSerializer)
class LocationView(BaseView):
    response_serializer_class = LocationResponseSerializer

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"],
        )
        serializer_data = [
            {
                "id": item["id"],
                "name": item["name"],
                "address": {
                    "city": item["city"],
                    "street": item["address"],  # todo: minus het huisnummer
                    "coordinates": {
                        "lat": item["coordinates"]["latitude"],
                        "lon": item["coordinates"]["longitude"],
                    },
                    # "number": item["address"], # Todo: extract number from address
                    "postcode": item["postalCode"],
                },
                "opening_times": {
                    "regular_hours": item["openingTimes"]["regularHours"],
                    "twentyfourseven": item["openingTimes"]["twentyfourseven"],
                    "exceptional_openings": item["openingTimes"]["exceptionalOpenings"],
                    "exceptional_closings": item["openingTimes"]["exceptionalClosings"],
                },
                # "charging_station_ids": [],
                "tariff_id": item["tariffId"],
                "available_sockets": item[
                    "chargingStationCount"
                ],  # Todo: get available sockets
                "total_sockets": item["chargingStationCount"],
            }
            for item in response_json
        ]
        serializer = self.response_serializer_class(data=serializer_data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)
