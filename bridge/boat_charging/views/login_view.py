import httpx
from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.login_serializers import (
    GuestLoginResponseSerializer,
)
from bridge.boat_charging.views.base_view import BaseView


class GuestLoginView(BaseView):
    response_serializer_class = GuestLoginResponseSerializer

    async def get(self, request, *args, **kwargs):
        payload = {"grant_type": "client_credentials", "scope": "infuse/admin"}
        headers = {"content-type": "application/x-www-form-urlencoded"}
        auth = httpx.BasicAuth(
            username=settings.BOAT_CHARGING_OAUTH_ID,
            password=settings.BOAT_CHARGING_OAUTH_SECRET,
        )
        response_json = await self.make_request(
            method="POST",
            endpoint=settings.BOAT_CHARGING_OAUTH_URL,
            body_data=payload,
            headers=headers,
            auth=auth,
        )

        serializer = self.response_serializer_class(data=response_json)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)
