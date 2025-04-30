import requests
from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView

from bridge.proxy.serializers import (
    AddressSearchRequestSerializer,
    WasteGuideRequestSerializer,
)


@method_decorator(cache_page(60 * 60 * 24), name="dispatch")
class WasteGuideView(GenericAPIView):
    authentication_classes = []
    serializer_class = WasteGuideRequestSerializer

    @extend_schema(parameters=[WasteGuideRequestSerializer])
    def get(self, request):
        self.get_serializer(data=request.query_params).is_valid(raise_exception=True)

        url = settings.WASTE_GUIDE_URL
        api_key = settings.WASTE_GUIDE_API_KEY
        response = requests.get(url, params=request.GET, headers={"X-Api-Key": api_key})
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )


@method_decorator(cache_page(60 * 60 * 24), name="dispatch")
class AddressSearchView(GenericAPIView):
    authentication_classes = []
    serializer_class = AddressSearchRequestSerializer

    @extend_schema(parameters=[AddressSearchRequestSerializer])
    def get(self, request):
        self.get_serializer(data=request.query_params).is_valid(raise_exception=True)

        url = settings.ADDRESS_SEARCH_URL
        # Since the query params are repetitive, we need to construct the list ourselves to avoid losing duplicate keys
        params = [(k, v) for k, vs in request.GET.lists() for v in vs]
        response = requests.get(
            url, params=params, headers={"Referer": "app.amsterdam.nl"}
        )
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )
