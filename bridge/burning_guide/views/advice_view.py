import logging

from rest_framework import generics, status
from rest_framework.response import Response

from bridge.burning_guide.serializers.advice import (
    AdviceRequestSerializer,
    AdviceResponseSerializer,
)
from bridge.burning_guide.services.rivm import RIVMService
from bridge.burning_guide.utils import (
    extend_schema_for_burning_guide as extend_schema,
)

logger = logging.getLogger(__name__)
rivm_client = RIVMService()


class BurningGuideAdviceView(generics.GenericAPIView):
    """
    Get burning guide properties for a given postal code
    """

    serializer_class = AdviceRequestSerializer

    @extend_schema(
        success_response=AdviceResponseSerializer,
        serializer_as_params=AdviceRequestSerializer,
    )
    def get(self, request, *args, **kwargs) -> Response:
        request_serializer = self.serializer_class(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        postal_code = data.get("postal_code")
        if not postal_code:
            raise Exception("Postal code should be provided")

        bbox = rivm_client.get_bbox_from_postal_code(postal_code=postal_code)
        validated_data = rivm_client.get_burning_guide_information(bbox=bbox)
        return Response(
            data=validated_data,
            status=status.HTTP_200_OK,
        )
