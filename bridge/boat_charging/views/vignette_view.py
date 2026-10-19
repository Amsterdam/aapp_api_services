from django.conf import settings
from rest_framework.response import Response

from bridge.boat_charging.serializers.vignette_serializers import (
    RequiredVignetteFieldSerializer,
    VerifyVignetteResponseSerializer,
    VignettesResponseSerializer,
)
from bridge.boat_charging.views.base_view import (
    BaseView,
    boat_charging_openapi_decorator,
)


class VignettesRetrieveCreateView(BaseView):
    requires_access_token = True

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() == "post":
            return RequiredVignetteFieldSerializer(*args, **kwargs)
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

        response_data = [create_vignette_response_data(item) for item in response_list]

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
        request_data = RequiredVignetteFieldSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        validated_data = request_data.validated_data

        request_payload = {
            "vignetNumber": validated_data["vignette_number"],
            "postcode": validated_data["postal_code"],
        }
        endpoint = settings.BOAT_CHARGING_ENDPOINTS["VIGNETTES"]
        response = await self.api_call(
            "post",
            endpoint=endpoint,
            body_data=request_payload,
        )

        response_data = create_vignette_response_data(response)

        response_serializer = VignettesResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=200)


class VignettesUpdateDeleteView(BaseView):
    requires_access_token = True

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() == "put":
            return RequiredVignetteFieldSerializer(*args, **kwargs)
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
            endpoint=f"{settings.BOAT_CHARGING_ENDPOINTS['VIGNETTES']}/{id}",
            body_data={
                "vignetNumber": validated_data["vignette_number"],
                "postcode": validated_data["postal_code"],
            },
        )

        response_data = [create_vignette_response_data(item) for item in response_list]

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

        endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['VIGNETTES']}/{id}"
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

        response = await self.api_call(
            "post",
            endpoint=f"{settings.BOAT_CHARGING_ENDPOINTS['VIGNETTES']}/verify",
            body_data=request_payload,
        )

        if response["status"] == "valid":
            response_data = {
                "status": response["status"],
                "expiration_date": response["validToDate"],
            }
        else:
            response_data = {
                "status": response["status"],
                "reason": response["reason"],
            }

        response_serializer = self.response_serializer_class(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=200)


def create_vignette_response_data(item):
    return {
        "vignette_number": item["vignetNumber"],
        "postal_code": item["postcode"],
        "id": item["id"],
        "boat_name": item.get("boatName"),
        "expiration_date": item["validToDate"],
    }
