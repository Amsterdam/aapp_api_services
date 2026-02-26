import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from contact.enums.services import Services
from contact.serializers.service_serializers import (
    ServiceMapResponseSerializer,
    ServiceMapsResponseSerializer,
    ToiletMapResponseSerializer,
)
from contact.services.toilets import ToiletService
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)

toilet_service = ToiletService()


class ServiceMapsView(APIView):
    response_serializer_class = ServiceMapsResponseSerializer

    @method_decorator(cache_page(60 * 60 * 24), name="dispatch")
    def get(self, request, *args, **kwargs):

        services = Services.choices()
        response_serializer = ServiceMapsResponseSerializer(services, many=True)
        return Response(response_serializer.data)


class ServiceMapView(APIView):
    response_serializer_class = ServiceMapResponseSerializer

    @method_decorator(cache_page(60 * 60 * 24), name="dispatch")
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
        data_service_class = Services.get_service_by_id(
            service_id
        )  # Check if service exists, will return None if not found
        if data_service_class is not None:
            data_service = data_service_class()
            response_payload = data_service.get_full_data()

            response_serializer = ToiletMapResponseSerializer(data=response_payload)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.validated_data)

        else:
            return Response(
                {"detail": "Service not found."}, status=status.HTTP_404_NOT_FOUND
            )
