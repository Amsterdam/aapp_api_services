import csv
import io
import logging

import requests
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.response import Response

from bridge.parking.serializers.parking_machine_serializers import (
    ParkingMachineListRequestSerializer,
    ParkingMachineListResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpointExternal
from bridge.parking.views.base_ssp_view import ssp_openapi_decorator

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 60), name="dispatch")
class ParkingMachineListView(generics.GenericAPIView):
    serializer_class = ParkingMachineListRequestSerializer
    response_serializer = ParkingMachineListResponseSerializer

    @ssp_openapi_decorator(
        response_serializer_class=response_serializer,
        requires_access_token=False,
        serializer_as_params=serializer_class,
    )
    def get(self, request, *args, **kwargs):
        response = requests.get(
            SSPEndpointExternal.PARKING_MACHINES_LIST.value, timeout=10
        )
        response.raise_for_status()

        f = io.StringIO(response.text)
        reader = csv.DictReader(f, delimiter=";")
        payload = []
        for row in reader:
            if row["GEB_DOMEIN"] == "363":  # 363 corresponds to Amsterdam
                payload.append(
                    {
                        "id": row.get("VERKOOPPUNT"),
                        "name": row.get("VKP_OMS"),
                        "lat": float(row.get("LAT")),
                        "lon": float(row.get("LON")),
                        "payment_area": row.get("GEBIED"),
                        "start_date": row.get("VKP_BEGIN"),
                    }
                )

        serializer = self.response_serializer(data=payload, many=True)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
