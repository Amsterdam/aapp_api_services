import logging
from typing import List

from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.settings_serializers import (
    SettingsResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)

logger = logging.getLogger(__name__)

SETTINGS_MAPPING = {
    "PreAuthorizationAmount": {
        "name": "pre_authorization_amount",
        "value_type": float,
    },
    "SessionCleanupEnabled": {
        "name": "session_cleanup_enabled",
        "value_type": bool,
    },
    "SessionExpiryHours": {
        "name": "session_expiry_hours",
        "value_type": int,
    },
    "SessionExpiryWarningHours": {
        "name": "session_expiry_warning_hours",
        "value_type": int,
    },
    "StandardFine": {
        "name": "standard_fine",
        "value_type": int,
    },
}


@boat_charging_openapi_decorator(
    response_serializer_class=SettingsResponseSerializer(many=True),
    requires_access_token=True,
)
class SettingsView(BaseView):
    response_serializer_class = SettingsResponseSerializer
    requires_access_token = True

    async def get(self, request, *args, **kwargs):
        response_json = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["SETTINGS"],
        )

        response_data = {}
        for key, setting in SETTINGS_MAPPING.items():
            if key not in [
                response_entry.get("name") for response_entry in response_json
            ]:
                logger.warning(f"Missing expected setting: {key}")
            else:
                response_data[setting["name"]] = self._get_settings_value(
                    response_json, key, setting["value_type"]
                )

        serializer = self.response_serializer_class(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)

    def _get_settings_value(
        self, response_json: List, key: str, value_type: bool | int | float | str
    ):
        """
        Helper method to extract and convert a setting value from the response JSON.
        """
        # find entry in list of dicts where 'key' matches the provided key
        for entry in response_json:
            if entry.get("name") == key:
                try:
                    return value_type(entry.get("value"))
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting setting {key} to {value_type}: {e}")
                    return None
