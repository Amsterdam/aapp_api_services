from django.forms.models import model_to_dict
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics
from rest_framework.response import Response

from waste.models import RecycleLocation
from waste.serializers.recycle_location_serializers import (
    RecycleLocationResponseSerializer,
)


@method_decorator(cache_page(60 * 60), name="dispatch")
class RecycleLocationsView(generics.ListAPIView):
    queryset = RecycleLocation.objects.all()
    serializer_class = RecycleLocationResponseSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        recycle_location_objects = list(queryset)
        recycle_location_dicts = [
            model_to_dict(location) for location in recycle_location_objects
        ]

        response_data = [
            self._rename_fields_for_serializer(data_item)
            for data_item in recycle_location_dicts
        ]

        serializer = self.get_serializer(response_data, many=True)
        return Response(serializer.data)

    @staticmethod
    def _rename_fields_for_serializer(data):
        data["lat"] = data["latitude"]
        data["lon"] = data["longitude"]
        data["cityDistrict"] = data["city_district"]
        data["additionLetter"] = data["addition_letter"]
        data["additionNumber"] = data["addition_number"]
        data["postcode"] = data["postal_code"]

        return data
