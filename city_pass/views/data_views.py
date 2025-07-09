import logging
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, mixins, status
from rest_framework.response import Response
from rest_framework.serializers import Serializer as DRFSerializer
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from city_pass import authentication, models
from city_pass.exceptions import (
    MijnAMSAPIException,
    MijnAMSInvalidDataException,
    MijnAMSRequestException,
)
from city_pass.serializers import data_serializers as serializers
from city_pass.views.extend_schema import extend_schema_with_access_token

logger = logging.getLogger(__name__)


class AbstractMijnAmsDataView(generics.RetrieveAPIView, ABC):
    """
    Abstract class that can be used for all calls to the Mijn Amsterdam Stadspas API.
    Override the get_source_api_path function to specify which endpoint
    with what path parameter should be called.
    """

    serializer_class: DRFSerializer = None  # Must be overwritten in subclasses
    serializer_many = True
    authentication_classes = [authentication.AccessTokenWithAdminNrAuthentication]

    def __init__(self):
        super().__init__()
        self.query_params = {}

    @abstractmethod
    def get_source_api_path(self, request) -> str:
        """This method should be overridden by subclasses to customize the source API path."""
        raise NotImplementedError(
            "This method should be overridden by subclasses to customize the source API path."
        )

    def process_response_content(self, content, request) -> None:
        """Optional method to do something extra with the content from the source API response."""

    def get(self, request, *args, **kwargs) -> Response:
        response_content = self.get_response_content(request, method="GET")
        self.process_response_content(response_content, request)
        serializer = self.serialize_response_content(response_content)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_response_content(self, request, method):
        source_api_path = self.get_source_api_path(request)
        source_api_url = urljoin(settings.MIJN_AMS_API_DOMAIN, source_api_path)
        headers = {settings.MIJN_AMS_API_KEY_HEADER: settings.MIJN_AMS_API_KEY_INBOUND}
        mijn_ams_response = self.make_request(headers, method, source_api_url)

        try:
            response_content = mijn_ams_response.json().get("content")
        except ValueError as e:
            logger.error(f"Invalid JSON received from Mijn Amsterdam API: {e}")
            raise MijnAMSInvalidDataException()

        if response_content is None:
            logger.error("No content received from Mijn Amsterdam API")
            raise MijnAMSInvalidDataException()

        return response_content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(MijnAMSAPIException),
        reraise=True,  # Reraise the MijnAMSAPIException after retries
    )
    def make_request(self, headers, method, source_api_url):
        try:
            mijn_ams_response = requests.request(
                method=method,
                url=source_api_url,
                headers=headers,
                params=self.query_params,
            )
            mijn_ams_response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Mijn Amsterdam API failed: {e}")
            raise MijnAMSAPIException()
        return mijn_ams_response

    def serialize_response_content(self, response_content) -> DRFSerializer:
        output_serializer = self.get_serializer(
            data=response_content, many=self.serializer_many
        )
        if not output_serializer.is_valid():
            logger.error(
                f"Mijn Amsterdam API data not in expected format: {output_serializer.errors}"
            )
            raise MijnAMSInvalidDataException("Received data not in expected format")
        return output_serializer


class PassesDataView(AbstractMijnAmsDataView):
    serializer_class = serializers.MijnAmsPassDataSerializer

    @extend_schema_with_access_token(
        success_response=serializer_class(many=True),
        exceptions=[MijnAMSAPIException, MijnAMSInvalidDataException],
    )
    def get(self, request, *args, **kwargs) -> Response:
        """Endpoint to retrieve all passes for the current user"""
        return super().get(request, *args, **kwargs)

    def get_source_api_path(self, request) -> str:
        session = request.user
        return urljoin(
            settings.MIJN_AMS_API_PATHS["PASSES"],
            session.encrypted_adminstration_no,
        )

    def process_response_content(self, content, request) -> None:
        session = request.user
        passes, budgets = [], []
        links = []
        Through = models.PassData.budgets.through
        for pass_data in content:
            budgets += [
                models.Budget(
                    code=budget["code"],
                    title=budget["title"],
                    description=budget.get("description", ""),
                )
                for budget in pass_data["budgets"]
            ]
            pass_obj = models.PassData(
                session=session,
                pass_number=pass_data.get("passNumber"),
                encrypted_transaction_key=pass_data.get("transactionsKeyEncrypted"),
            )
            passes.append(pass_obj)
            links += [(Through(passdata=pass_obj, budget=b)) for b in budgets]

        # Bulk update these passes in the database based on the passNumber field
        models.Budget.objects.bulk_create(
            budgets,
            update_conflicts=True,
            update_fields=["title", "description"],
            unique_fields=["code"],
        )
        models.PassData.objects.bulk_create(
            passes,
            update_conflicts=True,
            update_fields=["encrypted_transaction_key"],
            unique_fields=["pass_number", "session_id"],
        )
        Through.objects.bulk_create(
            links,
            ignore_conflicts=True,
        )


class AbstractTransactionsView(AbstractMijnAmsDataView):
    base_url: str = None

    def get_source_api_path(self, request) -> str:
        session = request.user
        pass_number = self.get_pass_number(request)
        if pass_number is None:
            logger.error("Pass number not provided in query parameters")
            raise MijnAMSRequestException(
                "Pass number not provided in query parameters"
            )

        try:
            encrypted_transaction_key = models.PassData.objects.get(
                session=session,
                pass_number=pass_number,
            ).encrypted_transaction_key
        except models.PassData.DoesNotExist:
            logger.error(
                f"Pass with pass number {pass_number} not found for user {session}"
            )
            url = reverse("city-pass-data-passes")
            raise MijnAMSInvalidDataException(
                f"Pass with pass number {pass_number} not found. Please refresh the passes list with the [{url}] endpoint."
            )

        return urljoin(
            self.base_url,
            encrypted_transaction_key,
        )

    def get_pass_number(self, request):
        pass_number = request.query_params.get("passNumber")
        return pass_number


class BudgetTransactionsView(AbstractTransactionsView):
    serializer_class = serializers.MijnAmsPassBudgetTransactionsSerializer
    base_url = settings.MIJN_AMS_API_PATHS["BUDGET_TRANSACTIONS"]

    @extend_schema_with_access_token(
        success_response=serializer_class(many=True),
        exceptions=[
            MijnAMSAPIException,
            MijnAMSInvalidDataException,
            MijnAMSRequestException,
        ],
        additional_params=[
            OpenApiParameter(
                name="passNumber",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Number of the pass",
                required=True,
            ),
            OpenApiParameter(
                name="budgetCode",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Budget code of the transaction",
                required=False,
            ),
        ],
    )
    def get(self, request, *args, **kwargs) -> Response:
        """Endpoint to retrieve all budget transactions for a specific pass"""
        self.query_params = {"budgetCode": request.query_params.get("budgetCode")}
        return super().get(request, *args, **kwargs)


class AanbiedingTransactionsView(AbstractTransactionsView):
    serializer_class = serializers.MijnAmsPassAanbiedingSerializer
    base_url = settings.MIJN_AMS_API_PATHS["AANBIEDING_TRANSACTIONS"]
    serializer_many = False

    @extend_schema_with_access_token(
        success_response=serializer_class,
        exceptions=[
            MijnAMSAPIException,
            MijnAMSInvalidDataException,
            MijnAMSRequestException,
        ],
        additional_params=[
            OpenApiParameter(
                name="passNumber",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Number of the pass",
                required=True,
            ),
        ],
    )
    def get(self, request, *args, **kwargs) -> Response:
        """Endpoint to retrieve all aanbieding transactions for a specific pass"""
        return super().get(request, *args, **kwargs)


class PassBlockView(mixins.CreateModelMixin, AbstractTransactionsView):
    base_url = settings.MIJN_AMS_API_PATHS["PASS_BLOCK"]
    http_method_names = ["put"]

    @extend_schema_with_access_token(
        success_response=serializers.MijnAmsPassBlockSerializer,
        exceptions=[
            MijnAMSAPIException,
            MijnAMSInvalidDataException,
            MijnAMSRequestException,
        ],
    )
    def put(self, request, *args, **kwargs) -> Response:
        self.get_response_content(request, method="POST")
        data = {"status": "BLOCKED"}
        return Response(data, status=status.HTTP_200_OK)

    def get_pass_number(self, request):
        pass_number = self.kwargs["pass_number"]
        return pass_number
