import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control, cache_page
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import status
from rest_framework.decorators import renderer_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils.openapi_utils import extend_schema_for_api_key
from waste.exceptions import WasteGuideException
from waste.renderers import ICSCalendarRenderer, PDFCalendarRenderer
from waste.serializers.waste_guide_serializers import (
    WasteRequestSerializer,
    WasteResponseSerializer,
)
from waste.services.waste_collection import WasteCollectionService
from waste.services.waste_collection_ics import WasteCollectionICSService
from waste.services.waste_collection_pdf import WasteCollectionPDFService

logger = logging.getLogger(__name__)


class WasteGuideView(APIView):
    serializer_class = WasteRequestSerializer
    response_serializer_class = WasteResponseSerializer

    @extend_schema_for_api_key(
        exceptions=[WasteGuideException],
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
        is_residential = waste_service.get_is_residential()
        is_collection_by_appointment = waste_service.get_is_collection_by_appointment()

        response_serializer = self.response_serializer_class(
            data={
                "waste_types": waste_types,
                "calendar": calendar,
                "is_residential": is_residential,
                "is_collection_by_appointment": is_collection_by_appointment,
            }
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(data=response_serializer.data, status=status.HTTP_200_OK)


@renderer_classes([PDFCalendarRenderer])
class WasteGuidePDFView(APIView):
    serializer_class = WasteRequestSerializer

    @extend_schema_for_api_key(
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

        waste_service = WasteCollectionPDFService(bag_nummeraanduiding_id)
        waste_service.get_validated_data()
        pdf = waste_service.get_pdf_calendar()

        pdf_bytes = bytes(pdf.output())

        response = Response(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename="afvalwijzer_kalender.pdf"'
        )
        return response


@method_decorator(cache_control(public=True, max_age=3600), name="dispatch")
@method_decorator(cache_page(60 * 60), name="dispatch")
@renderer_classes([ICSCalendarRenderer])
class WasteGuideCalendarIcsView(APIView):
    def get(self, request, *args, **kwargs):
        bag_nummeraanduiding_id = kwargs.get("bag_nummeraanduiding_id")
        if bag_nummeraanduiding_id is None:
            return Response(
                {"detail": "bag_nummeraanduiding_id is required."},
                status=400,
            )

        if not isinstance(bag_nummeraanduiding_id, str):
            return Response(
                {"detail": "bag_nummeraanduiding_id must be a string."},
                status=400,
            )

        waste_service = WasteCollectionICSService(bag_nummeraanduiding_id)
        waste_service.get_validated_data()
        calendar = waste_service.create_ics_calendar()

        response = Response(calendar, content_type="text/calendar; charset=utf-8")
        response["Content-Disposition"] = 'inline; filename="calendar.ics"'
        return response
