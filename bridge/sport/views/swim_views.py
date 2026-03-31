import logging

from bridge.sport.services.data_amsterdam_service import DataAmsterdamService
from rest_framework import generics, status
from rest_framework.response import Response


logger = logging.getLogger(__name__)
data_amsterdam_service = DataAmsterdamService()


class SwimLocationsView(generics.GenericAPIView):
    """
    Get swim locations
    """

    def get(self, request, *args, **kwargs) -> Response:
        locations = data_amsterdam_service.get_swim_locations_where_amsterdam_is_renting_out()

        return Response(
            data=locations,
            status=status.HTTP_200_OK,
        )
