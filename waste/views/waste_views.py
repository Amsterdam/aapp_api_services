import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control, cache_page
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils.openapi_utils import custom_extend_schema, extend_schema_for_api_key
from waste.exceptions import WasteGuideException
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


class WasteGuidePDFView(View):
    serializer_class = WasteRequestSerializer

    def get(self, request):
        serializer = self.serializer_class(data=request.GET)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return HttpResponse(
                '{"detail":"bag_nummeraanduiding_id is invalid."}',
                content_type="application/json",
                status=400,
            )
        bag_nummeraanduiding_id = serializer.validated_data["bag_nummeraanduiding_id"]

        waste_service = WasteCollectionPDFService(bag_nummeraanduiding_id)
        try:
            waste_service.get_validated_data()
        except WasteGuideException as e:
            return JsonResponse(
                {"detail": e.default_detail, "code": e.default_code},
                status=e.status_code,
            )
        pdf = waste_service.get_pdf_calendar()
        pdf_bytes = bytes(pdf.output())

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename="afvalwijzer_kalender.pdf"'
        )
        return response


class WasteGuidePDFSchemaView(APIView):
    authentication_classes = []

    @custom_extend_schema(
        default_exceptions=[WasteGuideException],
        request=WasteRequestSerializer,
        success_response={
            "content": {
                "application/pdf": {"schema": {"type": "string", "format": "binary"}}
            }
        },
        additional_params=[
            OpenApiParameter(
                "bag_nummeraanduiding_id",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        # This will never actually be used, only for OpenAPI documentation
        return Response(status=204)


@method_decorator(cache_control(public=True, max_age=3600), name="dispatch")
@method_decorator(cache_page(60 * 60), name="dispatch")
class WasteGuideCalendarIcsView(View):
    def get(self, request, *args, **kwargs):
        bag_nummeraanduiding_id = kwargs.get("bag_nummeraanduiding_id")
        if bag_nummeraanduiding_id is None:
            return HttpResponse(
                '{"detail":"bag_nummeraanduiding_id is required."}',
                content_type="application/json",
                status=400,
            )

        if not isinstance(bag_nummeraanduiding_id, str):
            return HttpResponse(
                '{"detail":"bag_nummeraanduiding_id must be a string."}',
                content_type="application/json",
                status=400,
            )

        waste_service = WasteCollectionICSService(bag_nummeraanduiding_id)
        try:
            waste_service.get_validated_data()
        except WasteGuideException as e:
            return JsonResponse(
                {"detail": e.default_detail, "code": e.default_code},
                status=e.status_code,
            )

        calendar = waste_service.create_ics_calendar()

        response = HttpResponse(
            str(calendar), content_type="text/calendar; charset=utf-8"
        )
        response["Content-Disposition"] = 'inline; filename="calendar.ics"'
        return response


class WasteGuideCalendarIcsSchemaView(APIView):
    authentication_classes = []

    @custom_extend_schema(
        default_exceptions=[WasteGuideException],
        request=WasteRequestSerializer,
        success_response={
            "content": {
                "text/calendar": {"schema": {"type": "string", "format": "ics"}}
            }
        },
        additional_params=[
            OpenApiParameter(
                "bag_nummeraanduiding_id",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                required=True,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        # This will never actually be used, only for OpenAPI documentation
        return Response(status=204)
