import json
import logging
import re
from urllib.error import HTTPError

import requests
from django.conf import settings
from django.db import connections
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from requests import JSONDecodeError
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from shapely.geometry import Point

from bridge.proxy.serializers import (
    AddressPostalAreaResponseSerializer,
    AddressSearchByCoordinateSerializer,
    AddressSearchByNameSerializer,
    AddressSearchRequestSerializer,
    AddressSearchResponseSerializer,
    WasteGuideRequestSerializer,
)
from bridge.utils import load_postal_area_shapes
from core.utils.openapi_utils import extend_schema_for_api_key

logger = logging.getLogger(__name__)


class EgisProxyView(GenericAPIView):
    http_method_names = ["get", "post", "patch", "delete"]
    base_url = settings.SSP_BASE_URL_V2

    def get(self, r, *a, **k):
        return self._forward(r, *a, **k)

    def post(self, r, *a, **k):
        return self._forward(r, *a, **k)

    def patch(self, r, *a, **k):
        return self._forward(r, *a, **k)

    def delete(self, r, *a, **k):
        return self._forward(r, *a, **k)

    def _forward(self, request, path):
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        params = [
            (k, v) for k, vs in request.query_params.lists() if k != "url" for v in vs
        ]
        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in {"host", "content-length", "x-api-key"}
        }
        data = request.body if request.method in {"POST", "PATCH", "DELETE"} else None
        r = requests.request(
            request.method,
            url,
            params=params,
            headers=headers,
            data=data,
            allow_redirects=True,
            timeout=30,
        )
        try:
            content = r.json()
        except JSONDecodeError:
            content = r.content
        resp = Response(content, status=r.status_code)
        return resp


class EgisProxyExternalView(EgisProxyView):
    base_url = settings.SSP_BASE_URL_EXTERNAL


@method_decorator(cache_page(60 * 60 * 24), name="get")
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


@method_decorator(cache_page(60 * 5), name="get")
class PollingStationsView(GenericAPIView):
    def get(self, request):
        url = settings.POLLING_STATIONS_URL
        response = requests.get(
            url,
            params=request.GET,
            auth=(settings.POLLING_STATIONS_USER, settings.POLLING_STATIONS_PW),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        for n, polling_station in enumerate(data):
            if not polling_station.get("categories"):
                continue
            categories = [
                p for p in polling_station["categories"] if p != "reading_aid"
            ]
            data[n]["categories"] = categories
        return Response(
            data,
            status=response.status_code,
        )


@method_decorator(cache_page(60 * 60 * 24), name="get")
class AddressSearchView(GenericAPIView):
    authentication_classes = []
    serializer_class = AddressSearchRequestSerializer

    @extend_schema(parameters=[AddressSearchRequestSerializer])
    def get(self, request):
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


@method_decorator(cache_page(60 * 60 * 24), name="get")
class AddressSearchAbstractView(GenericAPIView):
    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        params = self.get_params(data=serializer.validated_data)
        try:
            response = requests.get(
                settings.ADDRESS_SEARCH_URL,
                params=params,
                headers={"Referer": "app.amsterdam.nl"},
                timeout=5,
            )
            response.raise_for_status()
        except HTTPError as e:
            logger.error(f"HTTPError: {e}")
            return Response({"detail": "Upstream address service error"}, status=502)

        data = json.loads(response.content)
        if not data.get("response"):
            logger.error(f"Invalid response: {data}")
            return Response({"detail": "Upstream address service error"}, status=502)

        response_data = [
            self._rename_fields_for_serializer(data=data_item)
            for data_item in data["response"]["docs"]
        ]

        response_serializer = AddressSearchResponseSerializer(
            data=response_data, many=True
        )
        response_serializer.is_valid()
        return Response(response_serializer.data)

    def get_params(self, data):
        return [
            (
                "fl",
                "straatnaam huisnummer huisletter huisnummertoevoeging postcode woonplaatsnaam type nummeraanduiding_id centroide_ll",
            ),
            (
                "qf",
                "exacte_match^1 suggest^0.5 straatnaam^0.6 huisnummer^0.5 huisletter^0.5 huisnummertoevoeging^0.5",
            ),
            ("fq", "bron:BAG"),
            ("bq", "type:weg^1.5"),
            ("bq", "type:adres^1"),
        ]

    def _rename_fields_for_serializer(self, data):
        # get lat and long from coordinates
        coordinates = self._get_lat_and_lon_from_coordinates(data["centroide_ll"])
        # change naming of fields
        data["city"] = data["woonplaatsnaam"]
        data["street"] = data["straatnaam"]
        data["lat"] = coordinates[0]
        data["lon"] = coordinates[1]
        data["number"] = data.get("huisnummer", "")
        data["additionLetter"] = data.get("huisletter", "")
        data["additionNumber"] = data.get("huisnummertoevoeging", "")
        data["bagId"] = data.get("nummeraanduiding_id", "")

        return data

    @staticmethod
    def _get_lat_and_lon_from_coordinates(coordinates):
        if hasattr(coordinates, "coords"):
            lon, lat = coordinates.coords
            return lat, lon
        m = re.match(r"POINT\(\s*([-0-9.]+)\s+([-0-9.]+)\s*\)", coordinates)
        if not m:
            return None, None
        lon, lat = m.groups()
        return float(lat), float(lon)


class AddressSearchByNameView(AddressSearchAbstractView):
    serializer_class = AddressSearchByNameSerializer

    @extend_schema_for_api_key(
        success_response=AddressSearchResponseSerializer(many=True),
        additional_params=[AddressSearchByNameSerializer],
    )
    def get(self, request):
        return super().get(request)

    def get_params(self, data):
        params = super().get_params(data)
        params.append(("q", data.get("query")))

        params.append(("fq", "woonplaatsnaam:(amsterdam OR weesp)"))
        params.append(("rows", "20"))
        street = data.get("street_name")
        if street:
            params.append(("fq", f"straatnaam:{street}"))
            params.append(("fq", "type:adres"))
        else:
            params.append(("fq", "type:(weg OR adres)"))
        return params


class AddressSearchByCoordinateView(AddressSearchAbstractView):
    serializer_class = AddressSearchByCoordinateSerializer

    @extend_schema_for_api_key(
        success_response=AddressSearchResponseSerializer(many=True),
        additional_params=[AddressSearchByCoordinateSerializer],
    )
    def get(self, request):
        return super().get(request)

    def get_params(self, data):
        params = super().get_params(data)
        params.append(("lat", data["lat"]))
        params.append(("lon", data["lon"]))

        params.append(("fq", "type:adres"))
        params.append(("rows", "5"))
        return params


class AddressPostalAreaByCoordinateView(GenericAPIView):
    serializer_class = AddressSearchByCoordinateSerializer
    response_serializer_class = AddressPostalAreaResponseSerializer

    @extend_schema_for_api_key(
        success_response=AddressPostalAreaResponseSerializer,
        additional_params=[AddressSearchByCoordinateSerializer],
    )
    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        location_point = Point(data["lon"], data["lat"])

        postal_area_data = load_postal_area_shapes()

        for postal_area, shape in postal_area_data.items():
            if shape.contains(location_point):
                response_serializer = self.response_serializer_class(
                    data={"postal_area": postal_area}
                )
                response_serializer.is_valid(raise_exception=True)
                return Response(
                    data=response_serializer.data,
                    status=status.HTTP_200_OK,
                )

        return Response(
            data="No postal area found.",
            status=status.HTTP_404_NOT_FOUND,
        )


class HealthCheckView(GenericAPIView):
    authentication_classes = []

    def get(self, request, *args, **kwargs) -> Response:
        """Health Check"""
        try:
            connections["default"].cursor()
        except BaseException:
            return Response(
                {"status": "unready"}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response({"status": "ok"})
