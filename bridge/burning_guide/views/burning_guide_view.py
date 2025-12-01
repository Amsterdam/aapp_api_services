import logging

from rest_framework import generics, status
from rest_framework.response import Response

from bridge.burning_guide.clients.geodan import GeoDanClient
from bridge.burning_guide.clients.rivm import RIVMClient
from bridge.burning_guide.serializers.burning_guide import (
    BruningGuideResponseSerializer,
    BurningGuideRequestSerializer,
)
from bridge.burning_guide.utils import (
    calculate_bbox_from_wsg_coordinates,
)
from bridge.burning_guide.utils import (
    extend_schema_for_burning_guide as extend_schema,
)

logger = logging.getLogger(__name__)

geodan_client = GeoDanClient()
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

        # get address coordinates for given postal code
        address_id = geodan_client.get_address_id(postal_code=postal_code)
        address_coordinates = geodan_client.get_address_coordinates(
            address_id=address_id
        )

        # get i and j value for address coordinates
        bbox = calculate_bbox_from_wsg_coordinates(
            address_coordinates[0], address_coordinates[1]
        )

        # use i and je value to get address information
        response_payload = rivm_client.get_burning_guide_information(bbox=bbox)

        response_serializer = BruningGuideResponseSerializer(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK,
        )
