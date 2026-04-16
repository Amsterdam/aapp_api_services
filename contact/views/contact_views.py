import logging

from django.forms.models import model_to_dict
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.response import Response

from contact.models import CityOffice
from contact.serializers.contact_serializers import CityOfficeResultSerializer

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60), name="dispatch")
class CityOfficesView(generics.RetrieveAPIView):
    queryset = CityOffice.objects.all().order_by("order")
    serializer_class = CityOfficeResultSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        output_data = self.construct_response(queryset)
        output_serializer = self.get_serializer(output_data)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def construct_response(self, queryset):
        result = []
        for item in queryset:
            item_dict = model_to_dict(item)
            item_dict["street"] = item.street_name
            item_dict["number"] = item.street_number
            item_dict["postcode"] = item.postal_code
            result.append(item_dict)
        output_data = {"status": True, "result": result}
        return output_data


class HealthCheckView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        logger.info("Health check passed")
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
