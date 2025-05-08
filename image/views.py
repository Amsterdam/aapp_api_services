import hashlib
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.serializers.error_serializers import get_error_response_serializers
from image.models import ImageSet
from image.serializers import (
    ImageSetFromUrlRequestSerializer,
    ImageSetRequestSerializer,
    ImageSetSerializer,
)

logger = logging.getLogger(__name__)


class ImageSetCreateView(generics.CreateAPIView):
    """
    Endpoint to create a new image set. This endpoint is network isolated and only accessible from other backend services.

    The image is uploaded in three different formats to Azure Blob Storage and variants are created in the database.
    """

    serializer_class = ImageSetRequestSerializer

    @extend_schema(
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
                    "identifier": {
                        "type": "string",
                        "description": "Optional identifier for the image",
                        "required": False,
                    },
                },
                "required": ["image"],
            }
        },
        responses={
            200: ImageSetSerializer,
            **get_error_response_serializers([ValidationError]),
        },
    )
    def post(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        imageset = create_serializer.save()
        output_serializer = ImageSetSerializer(imageset)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class ImageSetFromUrlCreateView(generics.CreateAPIView):
    """
    Endpoint to create a new image set from a image URL.

    The image is uploaded in three different formats to Azure Blob Storage and variants are created in the database.
    The extra identifier is automatically generated as the SHA256 hash of the URL.
    If the image already exists (based on the identifier), it is directly returned.
    """

    serializer_class = ImageSetFromUrlRequestSerializer

    @extend_schema(
        request=ImageSetFromUrlRequestSerializer,
        responses={
            200: ImageSetSerializer,
            **get_error_response_serializers([ValidationError]),
        },
    )
    def post(self, request, *args, **kwargs):
        url = request.data.get("url")
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        image_set = ImageSet.objects.filter(identifier=url_hash).first()
        if not image_set:
            request_data = request.data.copy()
            request_data["identifier"] = url_hash
            create_serializer = self.get_serializer(data=request_data)
            create_serializer.is_valid(raise_exception=True)
            image_set = create_serializer.save()

        output_serializer = ImageSetSerializer(image_set)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class ImageSetDetailView(generics.RetrieveDestroyAPIView):
    queryset = ImageSet.objects.all()
    serializer_class = ImageSetSerializer
    lookup_field = "pk"
