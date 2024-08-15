import logging
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.serializers import Serializer as DRFSerializer

from city_pass import authentication, models, serializers

logger = logging.getLogger(__name__)

class MijnAMSRequestException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid request to source data'
    default_code = 'request_error'

class MijnAMSAPIException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Something went wrong during request to source data, see logs for more information'
    default_code = 'api_error'

class MijnAMSInvalidDataException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Received data not in expected format'
    default_code = 'invalid_data'


def extend_schema_with_error_responses(subclass_200_response, additional_params=None):
    """
    Helper function to merge base responses with subclass-specific responses.
    """
    schema = {
        "parameters": [
            OpenApiParameter(
                name=settings.ACCESS_TOKEN_HEADER,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description='Access token for authentication',
                required=True,
            ),
        ],
        "responses": {
            400: serializers.DetailResultSerializer,
            404: serializers.DetailResultSerializer,
            500: serializers.DetailResultSerializer,
        },
    }
    schema["parameters"] += additional_params or []
    schema["responses"] = {200: subclass_200_response, **schema["responses"]}
    return extend_schema(**schema)

class AbstractMijnAmsDataView(generics.RetrieveAPIView, ABC):
    """
    Abstract class that can be used for all calls to the Mijn Amsterdam Stadspas API.
    Override the get_source_api_path function to specify which endpoint
    with what path parameter should be called.
    """
    serializer_class: DRFSerializer = serializers.DetailResultSerializer  # Must be overwritten in subclasses

    def __init__(self):
        super().__init__()
        self.query_params = {}

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
            mijn_ams_response = requests.get(source_api_url, headers=headers, params=self.query_params)
            mijn_ams_response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Mijn Amsterdam API failed: {e}")
            raise MijnAMSAPIException()

        try:
            response_content = mijn_ams_response.json().get("content")
        except ValueError as e:
            logger.error(f"Invalid JSON received from Mijn Amsterdam API: {e}")
            raise MijnAMSInvalidDataException()

        if response_content is None:
            logger.error(f"No content received from Mijn Amsterdam API")
            raise MijnAMSInvalidDataException("No data found for this user")

        return response_content

    def serialize_response_content(self, response_content) -> DRFSerializer:
        output_serializer = self.get_serializer(data=response_content, many=True)
        if not output_serializer.is_valid():
            logger.error(f"Mijn Amsterdam API data not in expected format: {output_serializer.errors}")
            raise MijnAMSInvalidDataException("Received data not in expected format")
        return output_serializer


class PassesDataView(AbstractMijnAmsDataView):
    serializer_class = serializers.MijnAmsPassDataSerializer

    @extend_schema_with_error_responses(subclass_200_response=serializer_class(many=True))
    def get(self, request, *args, **kwargs) -> Response:
        """ Endpoint to retrieve all passes for the current user """
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
    serializer_class = serializers.MijnAmsPassBudgetTransactionsSerializer

    @extend_schema_with_error_responses(
        subclass_200_response=serializer_class(many=True),
        additional_params=[
            OpenApiParameter(
                name="passNumber",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Number of the pass',
                required=True,
            ),
            OpenApiParameter(
                name="budgetCode",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Budget code of the transaction',
                required=False,
            ),
        ]
    )
    def get(self, request, *args, **kwargs) -> Response:
        """ Endpoint to retrieve all budget transactions for a specific pass """
        self.query_params = {"budget_code": request.query_params.get("budgetCode")}
        return super().get(request, *args, **kwargs)

    def get_source_api_path(self, request) -> str:
        session = request.user
        pass_number = request.query_params.get("passNumber")
        if pass_number is None:
            logger.error(f"Pass number not provided in query parameters")
            raise MijnAMSRequestException("Pass number not provided in query parameters")

        try:
            encrypted_transaction_key = models.PassData.objects.get(
                session=session,
                pass_number=pass_number,
            ).encrypted_transaction_key
        except models.PassData.DoesNotExist:
            logger.error(f"Pass with pass number {pass_number} not found for user {session}")
            url = reverse("passes-data")
            raise MijnAMSAPIException(f"Pass with pass number {pass_number} not found. Please refresh the passes list with the [{url}] endpoint.")

        return urljoin(
            settings.MIJN_AMS_API_PATHS["BUDGET_TRANSACTIONS"],
            encrypted_transaction_key,
        )

    def get_response_content(self, request):
        # TODO: Test data is not yet visible, so we mock the response data for now
        _ = self.get_source_api_path(request)
        from city_pass.tests.test_data_views import TestBudgetTransactionsViews
        return TestBudgetTransactionsViews.mock_response_data