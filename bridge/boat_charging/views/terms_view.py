from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response

from bridge.boat_charging.serializers.terms_serializers import TermsResponseSerializer
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


@method_decorator(cache_page(60 * 60), name="get")  # 1 hour caching
@boat_charging_openapi_decorator(
    response_serializer_class=TermsResponseSerializer,
    accepts_access_token=False,
)
class TermsView(BaseView):
    response_serializer_class = TermsResponseSerializer

    async def get(self, request, *args, **kwargs):
        """Retrieve the latest terms content."""
        response = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["TERMS"],
            query_params={"lang": "nl"},
        )

        serializer = self.response_serializer_class(
            data={"content": response["html"], "version": response["version"]}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)
