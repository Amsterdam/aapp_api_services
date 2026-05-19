import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from news.models import DISTRICT_TYPE_CHOICES

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 60), name="get")
class DistrictsView(APIView):

    def get(self, request, *args, **kwargs):
        data = [
            {"label": district[0], "name": district[1]} for district in DISTRICT_TYPE_CHOICES
        ]
        return Response({"data": data}, status=status.HTTP_200_OK)
