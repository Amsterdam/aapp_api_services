import logging
from datetime import date, timedelta

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response

from bridge.sport.services.data_amsterdam_service import DataAmsterdamService
from bridge.sport.services.zwembaden_api_service import ZwembadenApiService
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)
data_amsterdam_service = DataAmsterdamService()
zwembaden_api_service = ZwembadenApiService()


class SwimLocationsView(generics.GenericAPIView):
    """
    Get swim locations
    """

    def get(self, request, *args, **kwargs) -> Response:
        locations = (
            data_amsterdam_service.get_swim_locations_where_amsterdam_is_renting_out()
        )

        return Response(
            data=locations,
            status=status.HTTP_200_OK,
        )


class SwimScheduleView(generics.GenericAPIView):
    """
    Get swim schedule for specific location
    """

    @extend_schema_for_api_key(
        success_response={},
        additional_params=[
            OpenApiParameter(
                "swim_location_name",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                "calendar_days",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
            ),
        ],
    )
    def get(self, request, swim_location_name: str) -> Response:

        calendar_days = int(request.query_params.get("calendar_days", 7))
        response_dict = {}

        today = date.today()
        for day_offset in range(calendar_days):
            day = today + timedelta(days=day_offset)
            day_str = str(day)
            logger.info(f"Fetching schedule for {swim_location_name} on {day}")
            schedule = zwembaden_api_service.get_schedule_for_date_and_location(
                date_str=day_str, location_name=swim_location_name
            )
            response_dict[day_str] = schedule

        return Response(
            data=response_dict,
            status=status.HTTP_200_OK,
        )


class SwimActivitiesView(generics.GenericAPIView):
    """
    Get swim activities for specific location
    """

    @extend_schema_for_api_key(
        success_response={},
        additional_params=[
            OpenApiParameter(
                "swim_location_name",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                required=True,
            ),
        ],
    )
    def get(self, request, swim_location_name: str) -> Response:

        response_dict = zwembaden_api_service.get_activities_for_location(
            location_name=swim_location_name
        )

        return Response(
            data=response_dict,
            status=status.HTTP_200_OK,
        )
