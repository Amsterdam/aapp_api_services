import logging

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
        output_data = {"status": True, "result": queryset}
        output_serializer = self.get_serializer(output_data)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class HealthCheckView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        logger.info("Health check passed")
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
