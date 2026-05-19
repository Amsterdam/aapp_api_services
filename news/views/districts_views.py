import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from news.models import DISTRICT_TYPE_CHOICES
from news.serializers.districts_serializers import DistrictListResponseSerializer

logger = logging.getLogger(__name__)

CITY_AREAS = [
    "weesp"
]  # list of city ares, used to prefix name with "Stadsgebied" instead of "Stadsdeel"


@method_decorator(cache_page(60 * 60), name="get")
class DistrictListView(APIView):
    serializer_class = DistrictListResponseSerializer

    def get(self, request, *args, **kwargs):

        data = []
        for label, name in DISTRICT_TYPE_CHOICES:
            if label in CITY_AREAS:
                name = f"Stadsgebied {name}"
            else:
                name = f"Stadsdeel {name}"
            data.append({"label": label, "name": name})

        serializer = self.serializer_class(data={"data": data})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
