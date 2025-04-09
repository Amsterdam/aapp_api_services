import requests
from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from bridge.proxy.serializers import (
    AddressSearchRequestSerializer,
    WasteGuideRequestSerializer,
)


@method_decorator(cache_page(60 * 60 * 24), name="dispatch")
class WasteGuideView(APIView):
    authentication_classes = []

    @extend_schema(
        parameters=[WasteGuideRequestSerializer],
    )
    def get(self, request):
        data = WasteGuideRequestSerializer(data=request.GET)
        data.is_valid(raise_exception=True)

        url = settings.WASTE_GUIDE_URL
        api_key = settings.WASTE_GUID_API_KEY
        response = requests.get(url, params=request.GET, headers={"X-Api-Key": api_key})
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )


@method_decorator(cache_page(60 * 60 * 24), name="dispatch")
class AddressSearchView(APIView):
    authentication_classes = []

    @extend_schema(
        parameters=[AddressSearchRequestSerializer],
    )
    def get(self, request):
        url = settings.ADDRESS_SEARCH_URL

        # Since the query params are repetitive, we need to construct the list ourselves to avoid losing duplicate keys
        params = []
        for key, values in request.GET.lists():
            for value in values:
                params.append((key, value))

        response = requests.get(
            url, params=params, headers={"Referer": "app.amsterdam.nl"}
        )
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )
