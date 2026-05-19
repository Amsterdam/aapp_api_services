import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from news.models import DISTRICT_TYPE_CHOICES

logger = logging.getLogger(__name__)

CITY_AREAS = ["weesp"]  # list of city ares,


@method_decorator(cache_page(60 * 60), name="get")
class DistrictListView(APIView):
    def get(self, request, *args, **kwargs):

        data = []
        for label, name in DISTRICT_TYPE_CHOICES:
            if label in CITY_AREAS:
                name = f"Stadsgebied {name}"
            else:
                name = f"Stadsdeel {name}"
            data.append({"label": label, "name": name})
        return Response({"data": data}, status=status.HTTP_200_OK)
