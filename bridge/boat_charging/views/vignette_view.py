from urllib.parse import urljoin

from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.vignette_serializers import (
    VerifyVignetteRequestSerializer,
    VerifyVignetteResponseSerializer,
    VignettesLinkRequestSerializer,
    VignettesListResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


class VignettesRetrieveCreateView(BaseView):
    requires_access_token = True

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() == "post":
            return VignettesLinkRequestSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @boat_charging_openapi_decorator(
        response_serializer_class=VignettesListResponseSerializer(many=True),
        accepts_access_token=True,
        requires_access_token=True,
    )
    async def get(self, request, *args, **kwargs):
        """Retrieve the list of vignettes."""
        response_list = await self.api_call(
            "get",
            endpoint=settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"],
        )

        response_data = [
            {
                "id": item["id"],
                "vignet_number": item["vignetNumber"],
                "boat_name": item.get("boatName"),
                "created_at": item["createdAt"],
            }
            for item in response_list
        ]

        response_serializer = VignettesListResponseSerializer(
            data=response_data, many=True
        )
        response_serializer.is_valid(raise_exception=True)

        serializer = response_serializer
        return Response(serializer.data, status=200)

    @boat_charging_openapi_decorator(
        response_serializer_class=None,
        accepts_access_token=True,
        requires_access_token=True,
    )
    async def post(self, request, *args, **kwargs):
        """Link a vignette to a user."""
        request_data = VignettesLinkRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        validated_data = request_data.validated_data

        request_payload = {
            "vignetNumber": validated_data["vignet_number"],
            "postcode": validated_data["postal_code"],
            "boatName": validated_data["boat_name"],
        }
        endpoint = settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]
        await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=request_payload,
        )

        return Response(status=200)


class VerifyVignetteView(BaseView):
    requires_access_token = False
    response_serializer_class = VerifyVignetteResponseSerializer
    serializer_class = VerifyVignetteRequestSerializer

    @boat_charging_openapi_decorator(
        response_serializer_class=VerifyVignetteResponseSerializer,
        accepts_access_token=False,
        requires_access_token=False,
    )
    async def post(self, request, *args, **kwargs):
        """Verify a vignette."""
        request_data = VerifyVignetteRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        validated_data = request_data.validated_data

        request_payload = {
            "vignetNumber": validated_data["vignet_number"],
            "postcode": validated_data["postal_code"],
        }
        endpoint = f"{urljoin(settings.BOAT_CHARGING_ENDPOINTS['VIGNETTES'], 'verify')}"
        response = await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=request_payload,
        )

        response_data = {
            "status": response.get("status"),
            "expiration_date": response.get("validToDate"),
        }

        response_serializer = self.response_serializer_class(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=200)
