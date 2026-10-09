import logging

import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from bridge.parking.serializers.vehicle_serializers import (
    VehicleInformationRequestSerializer,
    VehicleInformationResponseSerializer,
)
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)


class VehicleInformationView(generics.GenericAPIView):
    """
    Get vehicle information for a given licence plate number
    """

    serializer_class = VehicleInformationRequestSerializer

    @extend_schema_for_api_key(
        success_response=VehicleInformationResponseSerializer,
        serializer_as_params=VehicleInformationRequestSerializer,
    )
    def get(self, request, *args, **kwargs) -> Response:
        request_serializer = self.serializer_class(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        licence_plate = data.get("licence_plate")

        # transform licence plate to uppercase and remove dashes
        licence_plate = licence_plate.upper().replace("-", "")
        response = self._make_request(licence_plate)
        vehicle_information = response.json()

        # if there is no vehicle information, we still return a successful response to not clutter logging
        if not vehicle_information:
            success = False
            content = None
        else:
            success = True
            content = {
                "brand": vehicle_information[0].get("merk"),
                "type": vehicle_information[0].get("handelsbenaming"),
                "color": vehicle_information[0].get("eerste_kleur"),
            }

        response_serializer = VehicleInformationResponseSerializer(
            data={"success": success, "content": content}
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self, licence_plate: str) -> requests.Response:
        """Make the HTTP request to RDW"""
        try:
            response = requests.get(
                settings.RDW_BASE_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-App-Token": f"{settings.RDW_APP_TOKEN}",
                },
                params={
                    "kenteken": licence_plate,
                    "$select": "merk, handelsbenaming, eerste_kleur",
                },
                timeout=10,
            )

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch rdw data")
            raise
