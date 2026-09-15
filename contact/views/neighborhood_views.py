import logging
import math

from rest_framework import generics, status
from rest_framework.response import Response

from contact.models import NeighborhoodNotes
from contact.serializers.neighborhood_serializers import (
    CreateNeighborhoodNoteRequestSerializer,
    CreateNeighborhoodNoteResponseSerializer,
    ImageCreateRequestSerializer,
    ImageCreateResponseSerializer,
    RetrieveNeighborhoodNotesRequestSerializer,
    RetrieveNeighborhoodNotesResponseSerializer,
)
from core.services.image_set import ImageSetService
from core.utils.openapi_utils import (
    extend_schema_for_api_key,
    extend_schema_for_device_id,
)
from core.views.mixins import DeviceIdMixin

logger = logging.getLogger(__name__)
NOTE_RANGE_METERS = 200  # Define the range for neighborhood notes in meters.


def _distance_meters_haversine(lat1, lng1, lat2, lng2):
    radius = 6371000  # Earth radius in meters.
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


class NeighborhoodNoteImageUploadView(generics.GenericAPIView):
    serializer_class = ImageCreateRequestSerializer

    @extend_schema_for_api_key(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "format": "binary",
                        "description": "Image file to upload",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the image",
                        "required": False,
                    },
                },
                "required": ["image"],
            }
        },
        success_response=dict,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_data = ImageSetService().upload(
            image=request.data["image"], description=request.data.get("description")
        )
        image_data["image_set_id"] = image_data.pop("id")
        return Response(
            ImageCreateResponseSerializer(image_data).data, status=status.HTTP_200_OK
        )


class CreateRetrieveNeighborhoodNoteView(DeviceIdMixin, generics.GenericAPIView):
    """Create and retrieve neighborhood notes."""

    http_method_names = ["post", "get"]

    def initial(self, request, *args, **kwargs):
        self.device_id_required = request.method.lower() == "post"
        super().initial(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method.lower() == "get":
            return RetrieveNeighborhoodNotesRequestSerializer
        else:
            return CreateNeighborhoodNoteRequestSerializer

    @extend_schema_for_device_id(
        success_response=CreateNeighborhoodNoteResponseSerializer
    )
    def post(self, request, *args, **kwargs):
        """Create a new neighborhood note."""
        serializer = self.get_serializer(
            data=request.data, context={"external_device_id": self.device_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response(serializer.instance)

    def get_success_response(self, instance):
        serializer = CreateNeighborhoodNoteResponseSerializer({"note_id": instance.id})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema_for_api_key(
        success_response=RetrieveNeighborhoodNotesResponseSerializer,
        additional_params=[RetrieveNeighborhoodNotesRequestSerializer],
    )
    def get(self, request, *args, **kwargs):
        """Retrieve neighborhood notes based on latitude and longitude."""
        request_serializer = self.get_serializer(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        lat = data["lat"]
        lng = data["lng"]

        lat_delta = NOTE_RANGE_METERS / 111320
        cos_lat = max(0.000001, math.cos(math.radians(lat)))
        lng_delta = NOTE_RANGE_METERS / (111320 * cos_lat)

        candidate_notes = NeighborhoodNotes.objects.filter(
            lat__gte=lat - lat_delta,
            lat__lte=lat + lat_delta,
            lng__gte=lng - lng_delta,
            lng__lte=lng + lng_delta,
        ).prefetch_related("images")

        notes = [
            note
            for note in candidate_notes
            if _distance_meters_haversine(lat, lng, float(note.lat), float(note.lng))
            <= NOTE_RANGE_METERS
        ]
        response_serializer = RetrieveNeighborhoodNotesResponseSerializer(
            notes, many=True
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema_for_device_id(success_response=None)
class DeleteNeighborhoodNoteView(DeviceIdMixin, generics.GenericAPIView):
    """Delete a neighborhood note."""

    http_method_names = ["delete"]

    def delete(self, request, note_id, *args, **kwargs):
        try:
            note = NeighborhoodNotes.objects.get(
                id=note_id, external_device_id=self.device_id
            )
        except NeighborhoodNotes.DoesNotExist:
            return Response(
                {"detail": "Neighborhood note not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RetrieveOwnNeighborhoodNotesView(DeviceIdMixin, generics.GenericAPIView):
    """Retrieve all neighborhood notes created by the current device."""

    http_method_names = ["get"]

    @extend_schema_for_device_id(
        success_response=RetrieveNeighborhoodNotesResponseSerializer
    )
    def get(self, request, *args, **kwargs):
        notes = NeighborhoodNotes.objects.filter(
            external_device_id=self.device_id
        ).prefetch_related("images")
        serializer = RetrieveNeighborhoodNotesResponseSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
