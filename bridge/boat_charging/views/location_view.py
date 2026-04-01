from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from bridge.burning_guide.serializers.notification import (
    BurningGuideNotificationRequestSerializer,
    BurningGuideNotificationResponseSerializer,
)
from core.services.internal_http_client import InternalServiceSession
from core.utils.openapi_utils import extend_schema_for_api_key

internal_client = InternalServiceSession()


@extend_schema_for_api_key(success_response=BurningGuideNotificationResponseSerializer)
class LocationView(GenericAPIView):
    serializer_class = BurningGuideNotificationRequestSerializer

    def get(self, request, *args, **kwargs):
        response = internal_client.get(
            url=settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"],
            # headers={
            #     settings.API_KEY_HEADER: request.headers.get(settings.API_KEY_HEADER),
            # },  TODO: add bearer token
        )
        return Response(response.json(), status=response.status_code)
