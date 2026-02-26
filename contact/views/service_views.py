import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from contact.serializers.service_serializers import (
    ServiceMapResponseSerializer,
    ToiletMapResponseSerializer,
)
from contact.services.toilets import ToiletService
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)

toilet_service = ToiletService()


@method_decorator(cache_page(60 * 60 * 24), name="dispatch")
class ServiceMapView(APIView):
    response_serializer_class = ServiceMapResponseSerializer

    @extend_schema_for_api_key(
        success_response=ServiceMapResponseSerializer,
        additional_params=[
            OpenApiParameter(
                "service_id",
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True,
            )
        ],
    )
    def get(self, request, service_id: int):

        if (
            service_id == 1
        ):  # Currently we only have one service, which is toilets, so we check if the service_id is 1.
            # TODO: Update method when ticket to get all services is implemented.
            logger.info("Fetching data for service_id 1 (toilets)")
            response_payload = toilet_service.get_full_data()

            response_serializer = ToiletMapResponseSerializer(data=response_payload)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.validated_data)

        else:
            return Response(
                {"detail": "Service not found."}, status=status.HTTP_404_NOT_FOUND
            )
