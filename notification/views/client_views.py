from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response

from core.exceptions import InputDataException
from core.views.extend_schema import extend_schema_for_api_key as extend_schema
from notification.exceptions import MissingClientIdHeader
from notification.models import Client
from notification.serializers import (
    ClientRegisterPostSwaggerSerializer,
    ClientRegisterSerializer,
)


class ClientRegisterView(generics.GenericAPIView):
    """
    API view to register or unregister a client.
    """

    @extend_schema(
        request=ClientRegisterPostSwaggerSerializer,
        success_response=ClientRegisterSerializer,
        additional_params=[
            OpenApiParameter(
                settings.HEADER_CLIENT_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            )
        ],
        exceptions=[MissingClientIdHeader, InputDataException],
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new client with firebase token and os if client id is not known yet.
        Update client with firebase token and os if client is already known.
        """
        client_id = request.headers.get(settings.HEADER_CLIENT_ID)
        if not client_id:
            raise MissingClientIdHeader

        # Include 'client_id' in the serializer data
        request_data = request.data.copy()
        request_data["external_id"] = client_id

        # Retrieve the client if it exists
        client = Client.objects.filter(external_id=client_id).first()

        # Initialize the serializer with instance for update or None for create
        serializer = ClientRegisterSerializer(instance=client, data=request_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        additional_params=[
            OpenApiParameter(
                settings.HEADER_CLIENT_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=True,
            )
        ],
        exceptions=[MissingClientIdHeader],
        success_response={200: None},
    )
    def delete(self, request, *args, **kwargs):
        """
        Unregister a client by removing its Firebase token.
        """
        client_id = request.headers.get(settings.HEADER_CLIENT_ID)
        if not client_id:
            raise MissingClientIdHeader

        try:
            client = Client.objects.get(external_id=client_id)
        except Client.DoesNotExist:
            return Response(
                data="Client is not found, but that's okay",
                status=status.HTTP_200_OK,
            )

        # Remove the Firebase token
        client.firebase_token = None
        client.save()

        return Response("Registration removed", status=status.HTTP_200_OK)
