import logging

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
        lat = data.get("lat")
        lng = data.get("lng")
        logger.info(
            f"Retrieving neighborhood notes for lat={lat}, lng={lng}, but not using them now"
        )
        notes = NeighborhoodNotes.objects.all()
        serializer = RetrieveNeighborhoodNotesResponseSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        notes = NeighborhoodNotes.objects.filter(external_device_id=self.device_id)
        serializer = RetrieveNeighborhoodNotesResponseSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
