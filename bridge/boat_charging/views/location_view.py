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
        features = [self.get_location_feature_data(item) for item in response_json]

        serializer_data = {
            "type": "FeatureCollection",
            "features": features,
        }
        serializer = self.response_serializer_class(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)


@boat_charging_openapi_decorator(
    response_serializer_class=LocationDetailResponseSerializer,
    exceptions=[BoatChargingLocationNotFoundError],
)
class LocationDetailView(LocationView):
    response_serializer_class = LocationDetailResponseSerializer

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
