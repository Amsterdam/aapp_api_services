from rest_framework import generics, status
from rest_framework.response import Response

from contact.serializers.neighborhood_serializers import (
    CreateNeighborhoodNoteRequestSerializer,
    CreateNeighborhoodNoteResponseSerializer,
    ImageCreateRequestSerializer,
    ImageCreateResponseSerializer,
)
from core.services.image_set import ImageSetService
from core.utils.openapi_utils import (
    extend_schema_for_api_key,
    extend_schema_for_device_id,
)
from core.views.mixins import DeviceIdMixin


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


@extend_schema_for_device_id(success_response=CreateNeighborhoodNoteResponseSerializer)
class CreateNeighborhoodNoteView(DeviceIdMixin, generics.GenericAPIView):
    """Create a new neighborhood note."""

    http_method_names = ["post"]

    def get_serializer_class(self):
        return CreateNeighborhoodNoteRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"external_device_id": self.device_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response(serializer.instance)

    def get_success_response(self, instance):
        serializer = CreateNeighborhoodNoteResponseSerializer({"note_id": instance.id})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
