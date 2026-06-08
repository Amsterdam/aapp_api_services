import re
from pathlib import Path

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from bridge.boat_charging.serializers.terms_serializers import TermsResponseSerializer
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)

TERMS_FILENAME_RE = re.compile(r"^(?P<version>\d+)\.html$")


@method_decorator(cache_page(60 * 60), name="get")  # 1 hour caching
@boat_charging_openapi_decorator(
    response_serializer_class=TermsResponseSerializer,
    requires_access_token=False,
)
class TermsView(BaseView):
    response_serializer_class = TermsResponseSerializer
    terms_dir = Path(__file__).resolve().parent.parent / "terms"

    def get(self, request, *args, **kwargs):
        version, content = self.get_latest_terms_content()
        serializer = self.response_serializer_class(
            data={"content": content, "version": version}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    def get_latest_terms_content(self) -> tuple[int, str]:
        latest_version = None
        latest_file = None

        for file_path in self.terms_dir.iterdir():
            if not file_path.is_file():
                continue
            match = TERMS_FILENAME_RE.match(file_path.name)
            if not match:
                continue

            version = int(match.group("version"))
            if latest_version is None or version > latest_version:
                latest_version = version
                latest_file = file_path

        if latest_file is None or latest_version is None:
            raise NotFound("No terms versions found")

        return latest_version, latest_file.read_text(encoding="utf-8")
