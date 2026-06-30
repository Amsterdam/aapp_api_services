from typing import Any

from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.exceptions import (
    BoatChargingForbiddenError,
    BoatChargingLocationNotFoundError,
)
from bridge.boat_charging.serializers.location_serializers import (
    OPERATION_STATE_MAPPING,
    LocationDetailResponseSerializer,
    LocationListResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)
from bridge.utils import max_or_none


@boat_charging_openapi_decorator(
    response_serializer_class=LocationListResponseSerializer,
    requires_access_token=False,
)
class LocationView(BaseView):
    response_serializer_class = LocationListResponseSerializer
    paginated = True

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"],
        )
        features = [self.get_location_feature_data(item) for item in response_json]

        serializer_data = {
            "type": "FeatureCollection",
            "features": features,
        }
        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)

    def get_location_feature_data(self, item: dict[str, Any]) -> dict[str, Any]:
        item_dict = self.get_location_data(item)
        return {
            "type": "Feature",
            "properties": item_dict,
            "geometry": {
                "type": "Point",
                "coordinates": [
                    item["coordinates"]["longitude"],
                    item["coordinates"]["latitude"],
                ],
            },
        }

    def get_location_data(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Convert the location data from the API to the format expected by the frontend.
        """
        street, number = self.split_address(item["address"])

        status, max_kw = self._get_status_and_kw_from_sockets(item.get("sockets", []))

        return {
            "id": item["id"],
            "name": item["name"],
            "address": {
                "city": item["city"],
                "street": street,
                "coordinates": {
                    "lat": item["coordinates"]["latitude"],
                    "lon": item["coordinates"]["longitude"],
                },
                "postcode": item["postalCode"],
                **(
                    {"number": number} if number else {}
                ),  # number cannot be empty string, so only include if it is not empty
            },
            "opening_times": self.get_opening_times(item),
            "available_sockets": item.get("availableSockets", 0),
            "total_sockets": item.get("totalSockets", 0),
            "status": status,
            "max_kw": max_kw,
            "charging_stations_ids": item.get("chargingStationsIds", []),
            "charging_stations": [
                self.get_charging_station_data(cs)
                for cs in item.get("chargingStations", [])
            ],
            "tariff": self.get_tariff_data(item["tariff"])
            if "tariff" in item
            else None,
        }

    def _get_status_and_kw_from_sockets(
        self, sockets: list[dict[str, Any]]
    ) -> tuple[str, float | None]:
        """
        To determine the overall status and wattage of each location based on the statuses and wattages of its sockets, the logic described below is followed.

        There are three possible status values for a charging station:
        - "OPERATIVE": at least one connector at the location is operative
        - "OCCUPIED": all connectors at the location are occupied
        - "INOPERATIVE": no connector is operative and at least one connector is out of order

        The wattage of the location is determined by the connector with the highest wattage that is operative at the location,
        or if no connector is operative, the connector with the highest wattage that is out of order/occupied.
        """
        if not sockets:
            return "UNKNOWN", None

        available = [
            s.get("maxElectricPower")
            for s in sockets
            if OPERATION_STATE_MAPPING.get(s["status"], "UNKNOWN") == "OPERATIVE"
        ]
        occupied = [
            s.get("maxElectricPower")
            for s in sockets
            if OPERATION_STATE_MAPPING.get(s["status"], "UNKNOWN") == "OCCUPIED"
        ]
        out_of_order = [
            s.get("maxElectricPower")
            for s in sockets
            if OPERATION_STATE_MAPPING.get(s["status"], "UNKNOWN")
            not in ("OPERATIVE", "OCCUPIED")
        ]

        if available:
            overall_status = "OPERATIVE"
            max_kw = max_or_none(available)
            if max_kw is None:
                max_kw = max_or_none(occupied + out_of_order)
        elif occupied:
            overall_status = "OCCUPIED"
            max_kw = max_or_none(occupied + out_of_order)
        else:
            overall_status = "INOPERATIVE"
            max_kw = max_or_none(out_of_order)

        return overall_status, max_kw

    def get_charging_station_data(self, cs_json) -> dict:
        return {
            "id": cs_json["id"],
            "status": OPERATION_STATE_MAPPING.get(cs_json["status"], "UNKNOWN"),
            "location_id": cs_json["locationId"],
            "evses": [
                {
                    "id": evs["id"],
                    "display_name": f"{cs_json['id']}-{evs['id']}",
                    "ocpp_evse_id": evs["ocppEvseId"],
                    "evse_id": evs["evseId"],
                    "status": OPERATION_STATE_MAPPING.get(evs["status"], "UNKNOWN"),
                    "connectors": [
                        {
                            "connector_id": conn["connectorId"],
                            "max_amp": conn["maxAmp"],
                            "voltage": conn["voltage"],
                            "status": OPERATION_STATE_MAPPING.get(
                                conn["status"], "UNKNOWN"
                            ),
                        }
                        for conn in evs["connectors"]
                    ],
                }
                for evs in cs_json["evses"]
            ],
        }

    def get_tariff_data(self, tariff_json) -> dict:
        return {
            "id": tariff_json["id"],
            "energy_price_per_kwh": tariff_json["energyPricePerKwh"],
            "charging_time_price_per_hour": tariff_json["chargingTimePricePerHour"],
            "parking_time_price_per_hour": tariff_json["parkingTimePricePerHour"],
            "flat_fee_price": tariff_json["flatFeePrice"],
        }


@boat_charging_openapi_decorator(
    response_serializer_class=LocationDetailResponseSerializer,
    exceptions=[BoatChargingLocationNotFoundError],
    requires_access_token=False,
)
class LocationDetailView(LocationView):
    response_serializer_class = LocationDetailResponseSerializer
    paginated = False

    async def get(self, request, *args, **kwargs):
        location_id = self.get_safe_path_param(kwargs["location_id"])
        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{location_id}"
        try:
            response_json = await self.api_call("get", endpoint=endpoint)
        except BoatChargingForbiddenError:
            raise BoatChargingLocationNotFoundError()

        serializer_data = self.get_location_data(response_json)

        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)
