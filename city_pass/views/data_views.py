import logging
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.serializers import Serializer as DRFSerializer

from city_pass import authentication, models, serializers
from city_pass.serializers import MijnAmsPassBudgetSerializer

logger = logging.getLogger(__name__)

class MijnAMSAPIException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Something went wrong during request to source data, see logs for more information'
    default_code = 'mijn_ams_api_error'


class MijnAMSInvalidContentException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Invalid data received'
    default_code = 'mijn_ams_no_content'


class MijnAMSInvalidDataException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Received data not in expected format'
    default_code = 'mijn_ams_invalid_data'


def extend_schema_with_error_responses(subclass_200_response):
    """
    Helper function to merge base responses with subclass-specific responses.
    """
    schema = {
        "parameters": [
            OpenApiParameter(
                name=settings.ACCESS_TOKEN_HEADER,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description='Access token for authentication'
            ),
        ],
        "responses": {
            404: serializers.DetailResultSerializer,
            500: serializers.DetailResultSerializer,
        },
    }
    schema["responses"] = {200: subclass_200_response, **schema["responses"]}
    return extend_schema(**schema)

class AbstractMijnAmsDataView(generics.RetrieveAPIView, ABC):
    """
    Abstract class that can be used for all calls to the Mijn Amsterdam Stadspas API.
    Override the get_source_api_path function to specify which endpoint
    with what path parameter should be called.
    """
    serializer_class: DRFSerializer = serializers.DetailResultSerializer  # Must be overwritten in subclasses

    @abstractmethod
    def get_source_api_path(self, request) -> str:
        """This method should be overridden by subclasses to customize the source API path."""
        raise NotImplementedError("This method should be overridden by subclasses to customize the source API path.")

    def process_response_content(self, content, request) -> None:
        """Optional method to do something extra with the content from the source API response."""
        pass

    @authentication.authenticate_access_token
    def get(self, request, *args, **kwargs) -> Response:
        try:
            response_content = self.get_response_content(request)
            self.process_response_content(response_content, request)
            serializer = self.serialize_response_content(response_content)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except APIException as e:
            return Response({'detail': e.detail}, status=e.status_code)

    def get_response_content(self, request):
        source_api_path = self.get_source_api_path(request)
        source_api_url = urljoin(settings.MIJN_AMS_API_DOMAIN, source_api_path)
        headers = {settings.MIJN_AMS_API_KEY_HEADER: settings.MIJN_AMS_API_KEY}
        try:
            mijn_ams_response = requests.get(source_api_url, headers=headers)
            mijn_ams_response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Mijn Amsterdam API failed: {e}")
            raise MijnAMSAPIException()

        try:
            response_content = mijn_ams_response.json().get("content")
        except ValueError as e:
            logger.error(f"Invalid JSON received from Mijn Amsterdam API: {e}")
            raise MijnAMSInvalidContentException()

        if response_content is None:
            logger.error(f"No content received from Mijn Amsterdam API")
            raise MijnAMSInvalidContentException()

        return response_content

    def serialize_response_content(self, response_content) -> DRFSerializer:
        output_serializer = self.get_serializer(data=response_content, many=True)
        if not output_serializer.is_valid():
            logger.error(f"Mijn Amsterdam API data not in expected format: {output_serializer.errors}")
            raise MijnAMSInvalidDataException()
        return output_serializer


class PassesDataView(AbstractMijnAmsDataView):
    serializer_class = serializers.MijnAmsPassDataSerializer

    @extend_schema_with_error_responses(subclass_200_response=serializer_class(many=True))
    def get(self, request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    def get_source_api_path(self, request) -> str:
        session = request.user
        return urljoin(
            settings.MIJN_AMS_API_PATHS["PASSES"],
            session.encrypted_adminstration_no,
        )

    def process_response_content(self, content, request) -> None:
        session = request.user
        passes = [
            models.PassData(
                session=session,
                pass_number=pass_data.get("passNumber"),
                encrypted_transaction_key=pass_data.get("transactionsKeyEncrypted"),
            ) for pass_data in content
        ]
        # Bulk update these passes in the database based on the passNumber field
        models.PassData.objects.bulk_create(
            passes,
            update_conflicts=True,
            update_fields=['encrypted_transaction_key'],
            unique_fields=['pass_number', 'session_id'],
        )


class BudgetTransactionsView(AbstractMijnAmsDataView):
    serializer_class = MijnAmsPassBudgetSerializer

    @extend_schema_with_error_responses(subclass_200_response=serializer_class(many=True))
    def get(self, request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    def get_source_api_path(self, request) -> str:
        # TODO: read pass number & budget code from request query
        # query_params = request.query_params

        # TODO: find encrypted transaction key by pass number via session
        # session: models.Session = request.user
        # pass_data = session.passdata_set.objects.all()
        # encrypted_transaction_key = None

        # TODO: build source api path
        # - include budget code as query param
        # return urljoin(
        #     settings.MIJN_AMS_API_PATHS["BUDGET_TRANSACTIONS"],
        #     encrypted_transaction_key,
        # )
        pass
