import requests
from django.conf import settings
from django.http import HttpResponse
from django.views import View


class WasteGuideView(View):
    def dispatch(self, request, *args, **kwargs):
        url = settings.WASTE_GUIDE_URL
        api_key = settings.WASTE_GUID_API_KEY
        response = requests.request(
            method="GET",
            url=url,
            params=request.GET,
            headers={"X-Api-Key": api_key},
        )
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )


class AddressSearchView(View):
    def dispatch(self, request, *args, **kwargs):
        url = settings.ADDRESS_SEARCH_URL
        response = requests.request(
            method=request.method,
            url=url,
            params=request.GET,
        )
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )
