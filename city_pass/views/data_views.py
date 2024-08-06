import logging
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.http import HttpRequest
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from city_pass import authentication, models, serializers
from city_pass.utils import detail_message

logger = logging.getLogger(__name__)


class BaseMijnAmsDataView(generics.RetrieveAPIView, ABC):
    authentication_classes = [
        authentication.APIKeyAuthentication,
    ]

    mijn_ams_api_path = None

    @extend_schema(
        parameters=[
            authentication.access_token_header_param,
        ],
        responses={
            200: serializers.MijnAmsPassDataSerializer(many=True),
            403: serializers.DetailResultSerializer,
            404: serializers.DetailResultSerializer,
        },
    )
    @abstractmethod
    def get_source_api_path(self, request, session):
        """
        This method should be overridden by subclasses to customize the source API path.
        """
        pass

    @authentication.authenticate_access_token
    def get(self, request: HttpRequest, session: models.Session, *args, **kwargs):
        source_api_path = self.get_source_api_path(request, session)
        source_api_url = urljoin(
            settings.MIJN_AMS_API_DOMAIN,
            source_api_path,
        )
        headers = {"x-api-key": settings.MIJN_AMS_API_KEY}
        mijn_ams_response = requests.get(source_api_url, headers=headers)

        # Status code is in 400 or 500 range
        if 400 <= mijn_ams_response.status_code < 600:
            logger.error(
                f"Error occured during call to Mijn Amsterdam API: {mijn_ams_response.content=}"
            )
            return Response(
                detail_message(
                    "Something went wrong during request to source data, see logs for more information"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )

        response_content = mijn_ams_response.json().get("content")
        if response_content is None:
            logger.error(
                f"Expected content not found in call to Mijn Amsterdam API: {mijn_ams_response.content=}"
            )
            return Response(
                detail_message("Source data not in expected format"),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(response_content, status=status.HTTP_200_OK)


class PassesDataView(BaseMijnAmsDataView):
    def get_source_api_path(self, request, session):
        return urljoin(
            settings.MIJN_AMS_API_PATHS["PASSES"],
            session.encrypted_adminstration_no,
        )
