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
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 60 * 24), name="get")
class ServiceMapsView(APIView):
    response_serializer_class = ServiceMapsResponseSerializer

    def get(self, request, *args, **kwargs):

        services = Services.choices()
        response_serializer = ServiceMapsResponseSerializer(services, many=True)
        return Response(response_serializer.data)


@method_decorator(cache_page(60 * 60 * 24), name="get")
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
        data_service_class = Services.get_service_by_id(service_id)
        if data_service_class is None:
            # Service not found
            return Response(
                {"detail": "Service not found."}, status=status.HTTP_404_NOT_FOUND
            )
        if data_service_class.dataservice is None:
            # No data service available
            return Response(
                {"detail": "No data service available for this service."},
                status=status.HTTP_404_NOT_FOUND,
            )
        data_service = data_service_class.dataservice()
        response_payload = data_service.get_full_data()
        response_serializer = ToiletMapResponseSerializer(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.validated_data)
