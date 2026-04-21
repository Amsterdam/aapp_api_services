import asyncio
from urllib.parse import quote

from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.location_serializers import (
    LocationDetailResponseSerializer,
    LocationResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


@boat_charging_openapi_decorator(
    response_serializer_class=LocationResponseSerializer(many=True)
)
class LocationView(BaseView):
    response_serializer_class = LocationResponseSerializer
    paginated = True

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"],
        )
        serializer_data = [self.get_location_data(item) for item in response_json]
        serializer = self.response_serializer_class(data=serializer_data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)


@boat_charging_openapi_decorator(
    response_serializer_class=LocationDetailResponseSerializer
)
class LocationDetailView(LocationView):
    response_serializer_class = LocationDetailResponseSerializer
    paginated = False

    async def get(self, request, *args, **kwargs):
        location_id = self.get_safe_path_param(kwargs["location_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{location_id}"
        response_json = await self.api_call("get", endpoint=endpoint)
        serializer_data = self.get_location_data(response_json)

        # Enrich data with tariff
        tariff_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['TARIFFS']}/{quote(response_json['tariffId'], safe='')}"
        tariff_json = await self.api_call("get", endpoint=tariff_endpoint)
        serializer_data["tariff"] = self.get_tariff_data(tariff_json)

        # Enrich data with charging station ids
        charging_station_ids = response_json["chargingStationsIds"]
        tasks = [
            self.api_call(
                "get",
                endpoint=f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{quote(station_id, safe='')}",
            )
            for station_id in charging_station_ids
        ]
        charging_station_responses = await asyncio.gather(*tasks)
        serializer_data["charging_stations"] = [
            self.get_charging_station_data(charging_station_json)
            for charging_station_json in charging_station_responses
        ]

        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    def get_tariff_data(self, tariff_json) -> dict:
        return {
            "id": tariff_json["id"],
            "energy_price_per_kwh": tariff_json["energyPricePerKwh"],
            "charging_time_price_per_hour": tariff_json["chargingTimePricePerHour"],
            "parking_time_price_per_hour": tariff_json["parkingTimePricePerHour"],
            "flat_fee_price": tariff_json["flatFeePrice"],
        }

    def get_charging_station_data(self, cs_json) -> dict:
        return {
            "id": cs_json["id"],
            "status": cs_json["status"],
            "location_id": cs_json["locationId"],
            "evses": [
                {
                    "id": evs["id"],
                    "display_name": f"{cs_json['id']}-{evs['id']}",
                    "ocpp_evse_id": evs["ocppEvseId"],
                    "evse_id": evs["evseId"],
                    "status": evs["status"],
                    "connectors": [
                        {
                            "connector_id": conn["connectorId"],
                            "max_amp": conn["maxAmp"],
                            "voltage": conn["voltage"],
                            "status": conn["status"],
                        }
                        for conn in evs["connectors"]
                    ],
                }
                for evs in cs_json["evses"]
            ],
        }
