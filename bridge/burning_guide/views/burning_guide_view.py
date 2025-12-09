import logging

from rest_framework import generics, status
from rest_framework.response import Response

from bridge.burning_guide.clients.rivm import RIVMClient
from bridge.burning_guide.serializers.burning_guide import (
    BruningGuideResponseSerializer,
    BurningGuideRequestSerializer,
)
from bridge.burning_guide.utils import (
    extend_schema_for_burning_guide as extend_schema,
)

logger = logging.getLogger(__name__)

rivm_client = RIVMClient()


class BurningGuideView(generics.GenericAPIView):
    """
    Get burning guide properties for a given postal code
    """

    serializer_class = BurningGuideRequestSerializer

    @extend_schema(
        success_response=BruningGuideResponseSerializer,
        serializer_as_params=BurningGuideRequestSerializer,
    )
    def get(self, request, *args, **kwargs) -> Response:
        # get postal code from request
        request_serializer = self.serializer_class(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        postal_code = data.get("postal_code")
        if not postal_code:
            raise Exception("Postal code should be provided")

        bbox = rivm_client.get_bbox_from_postal_code(postal_code=postal_code)

        # use bbox to get address information
        response_payload = rivm_client.get_burning_guide_information(bbox=bbox)

        response_serializer = BruningGuideResponseSerializer(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )
