import json

import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from bridge.parking.exceptions import SSPCallError, SSPNotFoundError, SSPResponseError
from bridge.parking.serializers.permit_zone_serializer import (
    PermitZoneRequestSerializer,
)
from core.utils.openapi_utils import extend_schema_for_api_key


class ParkingPermitZoneView(generics.RetrieveAPIView):
    request_serializer_class = PermitZoneRequestSerializer

    @extend_schema_for_api_key(
        additional_params=[PermitZoneRequestSerializer],
        exceptions=[SSPCallError, SSPNotFoundError, SSPResponseError],
    )
    def get(self, request, *args, **kwargs):
        permit_zone = request.query_params.get("permit_zone")
        url = f"{settings.SSP_GEOJSON_URL}{permit_zone}"
        headers = {
            settings.SSP_GEOJSON_TOKEN_HEADER: settings.SSP_GEOJSON_TOKEN,
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise SSPNotFoundError("Permit zone not found")
        if response.status_code != 200:
            raise SSPCallError
        data = response.json()
        if not data.get("data") or not data["data"].get("calculatedGeometry"):
            raise SSPResponseError

        geojson_data = response.json()["data"]["calculatedGeometry"]
        geojson = json.loads(geojson_data)
        return Response(geojson, status=status.HTTP_200_OK)
