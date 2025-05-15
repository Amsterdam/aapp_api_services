import logging

import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.response import Response

from contact.exceptions import (
    FailedDependencyException,
    WaitingTimeSourceAvailabilityException,
)
from contact.models import CityOffice
from contact.serializers.contact_serializers import CityOfficeResultSerializer
from contact.serializers.waiting_time_serializers import WaitingTimeResultSerializer

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60), name="dispatch")
class CityOfficesView(generics.RetrieveAPIView):
    queryset = CityOffice.objects.all().order_by("order")
    serializer_class = CityOfficeResultSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset().prefetch_related(
            "openinghours_set", "openinghoursexception_set"
        )
        output_data = {"status": True, "result": queryset}
        output_serializer = self.get_serializer(output_data)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@method_decorator(cache_page(60), name="dispatch")
class WaitingTimesView(generics.RetrieveAPIView):
    serializer_class = WaitingTimeResultSerializer

    def get(self, request, *args, **kwargs):
        """
        Redirect call to Amsterdam "wachtijden" API.
        Enrich result with city office names.
        """

        try:
            waiting_times_result = requests.get(settings.WAITING_TIME_API, timeout=10)
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Waiting time API not available [{settings.WAITING_TIME_API=}, error={e}]"
            )
            raise WaitingTimeSourceAvailabilityException()

        if waiting_times_result.status_code != 200:
            raise FailedDependencyException()

        waiting_times_json = waiting_times_result.json()

        result = []
        for office in waiting_times_json:
            office_id = office["id"]
            internal_office_id = settings.CITY_OFFICE_LOOKUP_TABLE.get(office_id)
            if internal_office_id is None:
                logger.error(f"City office not found in lookup table: {office_id}")
                continue

            waiting_count = office["waiting"]
            waiting_time = office["waittime"]

            city_office = CityOffice.objects.filter(
                identifier=internal_office_id
            ).first()

            # Convert waiting time to minutes
            # If conversion fails, skip this office
            try:
                if waiting_time.lower() == "meer dan een uur":
                    waiting_time = 60
                elif waiting_time.lower() == "geen":
                    waiting_time = 0
                else:
                    waiting_time = int(waiting_time.split(" ")[0])
            except Exception:
                logger.error(
                    f"Waiting time data not in expected format: {waiting_time} [{office_id}]",
                )
                continue

            result.append(
                {
                    "title": city_office.title,
                    "identifier": city_office.identifier,
                    "queued": waiting_count,
                    "waitingTime": waiting_time,
                }
            )

        data = {
            "status": True,
            "result": result,
        }
        return Response(data, status=status.HTTP_200_OK)


class HealthCheckView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        logger.info("Health check passed")
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
