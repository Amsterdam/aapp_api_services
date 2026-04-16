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
    ServiceMapsRequestSerializer,
    ServiceMapsResponseSerializer,
    build_map_response_serializer,
)
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 60 * 24), name="get")
class ServiceMapsView(APIView):
    @extend_schema_for_api_key(
        success_response=ServiceMapsResponseSerializer(many=True),
        additional_params=[ServiceMapsRequestSerializer],
    )
    def get(self, request, *args, **kwargs):
        serializer = ServiceMapsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        module_source = serializer.validated_data["module_source"]
        services = Services.choices_as_list()

        # filter services on module_source
        services = [
            service for service in services if service["input_module"] == module_source
        ]

        response_serializer = ServiceMapsResponseSerializer(services, many=True)
        return Response(response_serializer.data)


# While testing, only cache for 15 minutes
# @method_decorator(cache_page(60 * 15), name="get")
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

        DynamicMapSerializer = build_map_response_serializer(
            properties=response_payload.get("properties_to_include", []),
            silent_properties=response_payload.get("silent_properties", []),
            filters=response_payload.get("filters", []),
            layers=response_payload.get("layers", []),
            list_property=response_payload.get("list_property", {}),
            include_icons=response_payload.get("icons_to_include", None) is not None,
        )

        response_serializer = DynamicMapSerializer(data=response_payload)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data)
