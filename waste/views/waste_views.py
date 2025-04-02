from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils.openapi_utils import extend_schema_for_api_key
from waste.serializers.waste_guide_serializers import (
    WasteRequestSerializer,
    WasteResponseSerializer,
)
from waste.services.waste_collection import WasteCollectionService


class WasteCalendarView(APIView):
    serializer_class = WasteRequestSerializer
    response_serializer_class = WasteResponseSerializer

    @extend_schema_for_api_key(
        success_response=WasteResponseSerializer,
        request=WasteRequestSerializer,
        additional_params=[
            OpenApiParameter(
                "bag_nummeraanduiding_id",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
            )
        ],
    )
    def get(self, request):
        serializer = self.serializer_class(data=request.GET)
        serializer.is_valid(raise_exception=True)
        bag_nummeraanduiding_id = serializer.validated_data["bag_nummeraanduiding_id"]

        waste_service = WasteCollectionService(bag_nummeraanduiding_id)
        waste_service.get_validated_data()
        calendar = waste_service.create_calendar()
        next_dates = waste_service.get_next_dates(calendar)
        waste_types = waste_service.get_waste_types(next_dates=next_dates)

        response_serializer = self.response_serializer_class(
            data={"waste_types": waste_types, "calendar": calendar}
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(data=response_serializer.data, status=status.HTTP_200_OK)
