import logging
from urllib.parse import urljoin

import requests
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from city_pass import authentication, serializers
from city_pass.utils import detail_message

logger = logging.getLogger(__name__)


class PassesDataView(generics.RetrieveAPIView):
    authentication_classes = [
        authentication.APIKeyAuthentication,
    ]

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
    def get(self, request, *args, **kwargs):
        token_authenticator = authentication.AccessTokenAuthentication()
        session, _ = token_authenticator.authenticate(request)

        source_api_path = urljoin(
            settings.MIJN_AMS_API_PATHS["PASSES"],
            session.encrypted_adminstration_no,
        )
        source_api_url = urljoin(
            settings.MIJN_AMS_API_DOMAIN,
            source_api_path,
        )
        headers = {"x-api-key": settings.MIJN_AMS_API_KEY}
        response = requests.get(source_api_url, headers=headers)

        # Status code is in 400 or 500 range
        if 400 <= response.status_code < 600:
            logger.error(
                f"Error occured during call to Mijn Amsterdam API: {response.content}"
            )
            return Response(
                detail_message(
                    "Something went wrong during request to source data, see logs for more information"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )

        response_content = response.json().get("content")
        if not response_content:
            return Response(
                detail_message("Source data not in expected format"),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(response_content, status=status.HTTP_200_OK)
