import logging

import requests
from django.conf import settings
from django.db.models import Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.utils.openapi_utils import custom_extend_schema, extend_schema_for_api_key
from modules.constants import MAPPING
from modules.exceptions import ReleaseNotFoundException
from modules.mock_data import MOCK_MAMS_RESPONSE
from modules.models import AppRelease, ReleaseModuleStatus
from modules.serializers.release_serializers import (
    MijnAmsterdamThemesSerializer,
    ReleaseModuleSerializer,
)
from modules.utils import VersionQueries

logger = logging.getLogger(__name__)


@extend_schema_for_api_key()
class MijnAmsterdamThemesView(generics.GenericAPIView):
    """
    View for retrieving the details of a specific app release.
    The release is identified by its version number, which is provided as a URL parameter.
    The view supports GET requests for retrieving release details.
    """

    serializer_class = MijnAmsterdamThemesSerializer
    lookup_field = "version"
    lookup_url_kwarg = "release_version"
    http_method_names = ["get"]

    def get_queryset(self):
        # keep only MAMS modules and order them by sort_order
        prefetch = Prefetch(
            "releasemodulestatus_set",
            queryset=ReleaseModuleStatus.objects.select_related(
                "module_version__module"
            )
            .filter(module_version__module__is_mams_theme=True)
            .order_by("sort_order"),
        )
        return AppRelease.objects.prefetch_related(prefetch)

    def get_object(self):
        version = self.kwargs.get(self.lookup_url_kwarg)
        if version == "latest":
            versions = list(AppRelease.objects.values_list("version", flat=True))
            if not versions:
                raise ReleaseNotFoundException
            version = VersionQueries.get_highest_version(versions)

        release = self.get_queryset().filter(version=version).first()
        if release is None:
            raise ReleaseNotFoundException(
                f"Release version '{version}' does not exist."
            )
        return release

    @custom_extend_schema(
        success_response=MijnAmsterdamThemesSerializer,
        description=(
            "Retrieve the themes of a specific app release. The release is identified by its version number, which is provided as a URL parameter. "
        ),
        default_exceptions=[ReleaseNotFoundException],
        additional_params=[
            OpenApiParameter(
                "release_version",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                description="The version number of the app release to retrieve. Use 'latest' to get the most recent release.",
                required=True,
            ),
            OpenApiParameter(
                name="AccessToken",
                description="Mijn Amsterdam Access Token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        access_token = request.headers.get("AccessToken")
        if not access_token:
            return Response(
                {"detail": "Access token is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Query theme modules directly for the selected release.
        release = self.get_object()
        theme_statuses = (
            ReleaseModuleStatus.objects.select_related("module_version__module")
            .filter(
                app_release=release,
                module_version__module__is_mams_theme=True,
            )
            .order_by("sort_order")
        )
        serialized_themes = ReleaseModuleSerializer(theme_statuses, many=True).data

        response_data = MOCK_MAMS_RESPONSE  # Replace with actual response

        # Index themes by module slug once to avoid repeatedly scanning the full list.
        themes_by_slug = {
            theme["moduleSlug"]: theme
            for theme in serialized_themes
            if "moduleSlug" in theme
        }

        relevant_themes = []
        for module_slug, fields in MAPPING.items():
            theme = themes_by_slug.get(module_slug)
            if not theme:
                continue

            content = {
                field: response_data[field]
                for field in fields
                if response_data.get(field)
            }

            if not content:
                continue

            # Keep module version metadata and append mapped content payload.
            relevant_themes.append({**theme, "content": content})

        response_data = {"themes": relevant_themes}

        return Response(response_data, status=status.HTTP_200_OK)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self, access_token, headers) -> requests.Response:
        """Make the HTTP request for toilet data with retries and a timeout."""
        url = settings.MIJN_AMS_API_DOMAIN + settings.MIJN_AMS_API_PATHS["ALL"]
        try:
            response = requests.get(
                url,
                cookies={"__MA-appSession": access_token},
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch data", extra={"url": url})
            raise
