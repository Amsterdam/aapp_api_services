from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from core.utils.openapi_utils import extend_schema_for_api_key
from waste.constants import (
    DISTRICT_PASS_NUMBER_MAPPING,
    DISTRICT_POSTAL_CODE_MAPPING,
    POSTAL_CODE_CONTAINER_NOT_PRESENT,
    District,
)
from waste.serializers.container_serializers import (
    WastePassNumberRequestSerializer,
    WastePassNumberResponseSerializer,
)


class WasteContainerPassNumberView(generics.RetrieveAPIView):
    serializer_class = WastePassNumberRequestSerializer

    @extend_schema_for_api_key(
        additional_params=[WastePassNumberRequestSerializer],
        success_response=WastePassNumberResponseSerializer,
        exceptions=[ValidationError, NotFound],
    )
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        pc_number, pc_letter = data["postal_code"]

        district = self.get_district(pc_number)
        if district is None:
            return Response("District not found", status=status.HTTP_404_NOT_FOUND)

        pass_number = self.get_pass_number(district)
        if pass_number is None:
            return Response("Pass number not found", status=status.HTTP_404_NOT_FOUND)

        has_container = self.has_container(pc_number, pc_letter)

        response_serializer = WastePassNumberResponseSerializer(
            {
                "district": district.value,
                "pass_number": pass_number,
                "has_container": has_container,
            }
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def get_district(self, postal_code_number: str) -> District:
        for district, ranges in DISTRICT_POSTAL_CODE_MAPPING.items():
            for start, end in ranges:
                if start <= postal_code_number <= end:
                    return district
        return None

    def get_pass_number(self, district: District) -> str:
        return DISTRICT_PASS_NUMBER_MAPPING.get(district)

    def has_container(self, postal_code_number: str, postal_code_letter: str) -> bool:
        areas_wo_container = None
        for code_range, areas in POSTAL_CODE_CONTAINER_NOT_PRESENT.items():
            start, end = code_range
            if start <= postal_code_number <= end:
                areas_wo_container = areas
                break

        if areas_wo_container is None:
            return True

        if postal_code_letter in areas_wo_container or len(areas_wo_container) == 0:
            return False

        return True
