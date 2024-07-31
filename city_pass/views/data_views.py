from urllib.parse import urljoin

import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from city_pass import authentication
from city_pass.views.generics import result_message


class PassesDataView(generics.RetrieveAPIView):
    authentication_classes = [
        authentication.APIKeyAuthentication,
    ]
    serializer_class = None

    def get(self, request, *args, **kwargs):
        session, _ = authentication.authenticate_access_token(request)

        source_api_url = urljoin(
            settings.MIJN_AMS_API_DOMAIN,
            settings.MIJN_AMS_API_PATHS["PASSES"],
            session.encrypted_adminstration_no,
        )
        headers = {"x-api-key": settings.MIJN_AMS_API_KEY}

        result = requests.get(source_api_url, headers=headers)
        # Status code is on 300 or 400 range
        if 300 <= result.status_code < 500:
            return Response(
                # TODO: What to return here?
                # Get data from response and pass through as data?
                None,
                status=result.status_code,
            )
        # Status code is on 500 range
        elif 500 <= result.status_code < 600:
            return Response(
                result_message("Source could not be reached by Mijn Amsterdam"),
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(result.data, status=status.HTTP_200_OK)
