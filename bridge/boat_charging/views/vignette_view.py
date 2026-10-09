from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.vignette_serializers import (
    RequiredVignetteFieldSerializer,
    VerifyVignetteResponseSerializer,
    VignettesLinkRequestSerializer,
    VignettesResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


def build_vignettes_endpoint(path: str = "") -> str:
    base_endpoint = settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"].rstrip("/")
    if not path:
        return base_endpoint
    return f"{base_endpoint}/{path.lstrip('/')}"


class VignettesRetrieveCreateView(BaseView):
    requires_access_token = True

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() == "post":
            return VignettesLinkRequestSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @boat_charging_openapi_decorator(
        response_serializer_class=VignettesResponseSerializer(many=True),
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
                "vignette_number": item["vignetNumber"],
                "boat_name": item.get("boatName"),
                "created_at": item["createdAt"],
            }
            for item in response_list
        ]

        response_serializer = VignettesResponseSerializer(data=response_data, many=True)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=200)

    @boat_charging_openapi_decorator(
        response_serializer_class=VignettesResponseSerializer,
        accepts_access_token=True,
        requires_access_token=True,
    )
    async def post(self, request, *args, **kwargs):
        """Link a vignette to a user."""
        request_data = VignettesLinkRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        validated_data = request_data.validated_data

        request_payload = {
            "vignetNumber": validated_data["vignette_number"],
            "postcode": validated_data["postal_code"],
            "boatName": validated_data.get("boat_name"),
        }
        endpoint = settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]
        response = await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=request_payload,
        )

        response_data = {
            "id": response["id"],
            "vignette_number": response["vignetNumber"],
            "boat_name": response.get("boatName"),
            "created_at": response["createdAt"],
        }

        response_serializer = VignettesResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=200)


class VignettesUpdateDeleteView(BaseView):
    requires_access_token = True

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() == "put":
            return VignettesLinkRequestSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @boat_charging_openapi_decorator(
        response_serializer_class=VignettesResponseSerializer(many=True),
        accepts_access_token=True,
        requires_access_token=True,
    )
    async def put(self, request, *args, **kwargs):
        """Update a vignette."""
        id = kwargs.get("id")
        request_data = self.get_serializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        validated_data = request_data.validated_data

        response_list = await self.api_call(
            "put",
            endpoint=build_vignettes_endpoint(id),
            body_data={
                "vignetNumber": validated_data["vignette_number"],
                "postcode": validated_data["postal_code"],
                "boatName": validated_data.get("boat_name"),
            },
        )

        response_data = [
            {
                "id": item["id"],
                "vignette_number": item["vignetNumber"],
                "boat_name": item.get("boatName"),
                "created_at": item["createdAt"],
            }
            for item in response_list
        ]

        response_serializer = VignettesResponseSerializer(data=response_data, many=True)
        response_serializer.is_valid(raise_exception=True)

        serializer = response_serializer
        return Response(serializer.data, status=200)

    @boat_charging_openapi_decorator(
        response_serializer_class=None,
        accepts_access_token=True,
        requires_access_token=True,
    )
    async def delete(self, request, *args, **kwargs):
        """Unlink a vignette from a user."""
        id = kwargs.get("id")

        endpoint = build_vignettes_endpoint(id)
        await self.api_call(
            "delete",
            endpoint=endpoint,
        )

        return Response(status=204)


class VerifyVignetteView(BaseView):
    requires_access_token = False
    response_serializer_class = VerifyVignetteResponseSerializer
    serializer_class = RequiredVignetteFieldSerializer

    @boat_charging_openapi_decorator(
        response_serializer_class=VerifyVignetteResponseSerializer,
        accepts_access_token=False,
        requires_access_token=False,
    )
    async def post(self, request, *args, **kwargs):
        """Verify a vignette."""
        request_data = RequiredVignetteFieldSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        validated_data = request_data.validated_data

        request_payload = {
            "vignetNumber": validated_data["vignette_number"],
            "postcode": validated_data["postal_code"],
        }
        endpoint = build_vignettes_endpoint("verify")
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
