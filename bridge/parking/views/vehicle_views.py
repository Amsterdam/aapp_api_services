import logging

import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from bridge.burning_guide.utils import (
    extend_schema_for_burning_guide as extend_schema,
)
from bridge.parking.serializers.vehicle_serializers import (
    VehicleInformationRequestSerializer,
    VehicleInformationResponseSerializer,
)

logger = logging.getLogger(__name__)


class VehicleInformationView(generics.GenericAPIView):
    """
    Get vehicle information for a given licence plate number
    """

    serializer_class = VehicleInformationRequestSerializer

    @extend_schema(
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
        logger.info(f"Fetching vehicle information for licence plate: {licence_plate}")
        response = self._make_request(licence_plate)
        vehicle_information = response.json()
        logger.info(f"Vehicle information fetched: {vehicle_information}")

        # it there is no vehicle information, we still return a successful response to not clutter logging
        if not vehicle_information:
            return Response(
                data={"success": False, "content": {}},
                status=status.HTTP_200_OK,
            )

        # Map the RDW response to the expected vehicle information format
        vehicle_information = {
            "success": True,
            "content": {
                "brand": vehicle_information.get("merk"),
                "type": vehicle_information.get("handelsbenaming"),
                "color": vehicle_information.get("eerste_kleur"),
            },
        }
        return Response(
            data=vehicle_information,
            status=status.HTTP_200_OK,
        )

    # @retry(
    #     stop=stop_after_attempt(3),
    #     wait=wait_fixed(2),
    #     retry=retry_if_exception_type(requests.exceptions.RequestException),
    #     reraise=True,  # Reraise the RequestException after retries
    # )
    def _make_request(self, licence_plate: str) -> requests.Response:
        """Make the HTTP request to RDW"""

        url = f"{settings.RDW_BASE_URL}"
        logger.info(f"Making request to URL: {url}, for licence plate: {licence_plate}")
        try:
            response = requests.get(
                url,
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
            logger.info(
                f"Made request to URL: {url}, for licence plate: {licence_plate}"
            )

            response.raise_for_status()
            logger.info(
                f"Successfully fetched vehicle information for licence plate: {licence_plate}"
            )
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch data", extra={"url": url})
            raise
