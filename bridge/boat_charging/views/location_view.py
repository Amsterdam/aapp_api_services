import asyncio
from collections import defaultdict
from urllib.parse import quote

from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.exceptions import (
    BoatChargingForbiddenError,
    BoatChargingLocationNotFoundError,
)
from bridge.boat_charging.serializers.location_serializers import (
    LocationDetailResponseSerializer,
    LocationListResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)
from core.utils.caching_utils import cache_function


@boat_charging_openapi_decorator(
    response_serializer_class=LocationListResponseSerializer
)
class LocationView(BaseView):
    response_serializer_class = LocationListResponseSerializer
    paginated = True

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"],
        )
        location_status_kw_mapping = await self.get_location_statuses_and_kw()
        features = [
            self.get_location_feature_data(item, location_status_kw_mapping)
            for item in response_json
        ]
        serializer_data = {
            "type": "FeatureCollection",
            "features": features,
        }
        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)

    @cache_function(timeout=60, ignore_first_arg=True)
    async def get_location_statuses_and_kw(self) -> dict[str, dict[str, str | None]]:
        """
        1. Fetch data of charging stations. Each charging station has a list of evses and each evse has a list of connectors.
        2. Iterate through the connectors per charging station and check the status and wattage of each connector.
        3. Append the status and wattage of each connector to a list of statuses for the location that the charging station belongs to.
        4. Determine the overall status and wattage of the location based on the list of statuses of its connectors.
        """

        data = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"],
            paginated=True,
        )

        location_connectors = defaultdict(list)
        for item in data:
            location_id = item["locationId"]

            evses = item.get("evses", [])
            for evs in evses:
                connectors = evs.get("connectors", [])
                for conn in connectors:
                    status = conn.get("status")
                    wattage = conn.get("maxElectricPower")
                    location_connectors[location_id].append((status, wattage))

        return self.determine_overall_status_and_wattage(location_connectors)

    def determine_overall_status_and_wattage(
        self, location_connectors: defaultdict[str, list[tuple[str, int]]]
    ) -> dict[str, dict[str, str | None]]:
        """
        To determine the overall status and wattage of each location based on the statuses and wattages of its connectors, the logic described below is followed.

        There are three possible status values for a charging station:
        - "OPERATIVE": at least one connector at the location is available
        - "OCCUPIED": all connectors at the location are occupied
        - "INOPERATIVE": no connector is available and at least one connector is out of order

        The wattage of the location is determined by the connector with the highest wattage that is available at the location,
        or if no connector is available, the connector with the highest wattage that is out of order/not available.
        """
        # Determine overall status and wattage per location
        result = {}

        for location_id, connectors in location_connectors.items():
            available = [(s, kw) for s, kw in connectors if s == "AVAILABLE"]
            occupied = [(s, kw) for s, kw in connectors if s == "OCCUPIED"]
            out_of_order = [
                (s, kw) for s, kw in connectors if s not in ("AVAILABLE", "OCCUPIED")
            ]

            if available:
                overall_status = "OPERATIVE"
                # check if any wattage values are available for the available connectors before calculating the best wattage
                wattage_defined = [kw for _, kw in available if kw is not None]
                best_wattage = max(wattage_defined) if wattage_defined else None
            elif out_of_order:
                overall_status = "INOPERATIVE"
                wattage_defined_out_of_order = [
                    kw for _, kw in out_of_order if kw is not None
                ]
                wattage_defined_occupied = [kw for _, kw in occupied if kw is not None]
                best_wattage = (
                    max(wattage_defined_out_of_order + wattage_defined_occupied)
                    if (wattage_defined_out_of_order + wattage_defined_occupied)
                    else None
                )
            else:
                # All connectors are occupied
                overall_status = "OCCUPIED"
                wattage_defined = [kw for _, kw in occupied if kw is not None]
                best_wattage = max(wattage_defined) if wattage_defined else None

            result[location_id] = {
                "status": overall_status,
                "max_kw": best_wattage / 1000
                if best_wattage
                else None,  # Convert W to kW
            }

        return result


@boat_charging_openapi_decorator(
    response_serializer_class=LocationDetailResponseSerializer,
    exceptions=[BoatChargingLocationNotFoundError],
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

        # Enrich data with tariff (if available)
        if "tariffId" not in response_json:
            # tariffId not available
            serializer_data["tariff"] = None
        else:
            try:
                tariff_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['TARIFFS']}/{quote(response_json['tariffId'], safe='')}"
                tariff_json = await self.api_call("get", endpoint=tariff_endpoint)
                serializer_data["tariff"] = self.get_tariff_data(tariff_json)
            except BoatChargingForbiddenError:
                # tariffId is available but tariff details cannot be accessed
                serializer_data["tariff"] = None

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

        # Enrich data with overall location status and wattage based on the charging stations' connectors
        location_status_kw_mapping = await self.get_location_statuses_and_kw()
        if location_id in location_status_kw_mapping:
            serializer_data["status"] = location_status_kw_mapping[location_id][
                "status"
            ]
            serializer_data["max_kw"] = location_status_kw_mapping[location_id][
                "max_kw"
            ]
        else:
            serializer_data["status"] = "UNKNOWN"
            serializer_data["max_kw"] = None

        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)

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
