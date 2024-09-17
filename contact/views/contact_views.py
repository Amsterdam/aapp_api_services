import logging

import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from contact.exceptions import (
    CityOfficeDataException,
    WaitingTimeDataException,
    WaitingTimeSourceAvailablityException,
)
from contact.models import CityOffice, OpeningHours, OpeningHoursException
from contact.serializers.contact_serializers import (
    CityOfficeResultSerializer,
    WaitingTimeResultSerializer,
)

logger = logging.getLogger(__name__)


def sort_list_of_dicts(items, key=None, sort_order="asc"):
    """Sort list of dictionaries"""
    if key is None:
        return items

    reverse = sort_order == "desc"

    if reverse is True:
        result = sorted(items, key=lambda x: (x[key] is not None, x[key]), reverse=True)
    else:
        result = sorted(items, key=lambda x: (x[key] is None, x[key]))
    return result


def get_opening_hours(identifier):
    """Get opening hours"""
    regular = [
        {
            "dayOfWeek": x.day_of_week,
            "opening": {"hours": x.opens_hours, "minutes": x.opens_minutes},
            "closing": {"hours": x.closes_hours, "minutes": x.closes_minutes},
        }
        for x in list(OpeningHours.objects.filter(city_office_id=identifier).all())
    ]
    exceptions = [
        {
            "date": x.date,
            "opening": {"hours": x.opens_hours, "minutes": x.opens_minutes},
            "closing": {"hours": x.closes_hours, "minutes": x.closes_minutes},
        }
        if x.opens_hours is not None
        else {"date": x.date}
        for x in list(
            OpeningHoursException.objects.filter(city_office_id=identifier).all()
        )
    ]
    return {"regular": regular, "exceptions": exceptions}


class CityOfficesView(generics.RetrieveAPIView):
    queryset = CityOffice.objects.all()
    serializer_class = CityOfficeResultSerializer

    def get(self, request, *args, **kwargs):
        offices = self.get_queryset()
        data = []
        for office in offices:
            opening_hours = get_opening_hours(office.identifier)
            city_office = {
                "identifier": office.identifier,
                "title": office.title,
                "image": office.images,
                "address": {
                    "streetName": office.street_name,
                    "streetNumber": office.street_number,
                    "postalCode": office.postal_code,
                    "city": office.city,
                },
                "addressContent": office.address_content,
                "coordinates": {"lat": office.lat, "lon": office.lon},
                "directionsUrl": office.directions_url,
                "appointment": office.appointment,
                "visitingHoursContent": office.visiting_hours_content,
                "visitingHours": opening_hours,
                "order": office.order,
            }
            data.append(city_office)

        result = sort_list_of_dicts(data, key="order", sort_order="asc")

        output_serializer = self.get_serializer(data={"status": True, "result": result})
        if not output_serializer.is_valid():
            logger.error(
                f"City office data not in expected format: {output_serializer.errors}"
            )
            raise CityOfficeDataException()

        return Response(output_serializer.data, status=status.HTTP_200_OK)


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
            raise WaitingTimeSourceAvailablityException()

        if waiting_times_result.status_code != 200:
            logger.error(
                f"Waiting time API not available [{settings.WAITING_TIME_API=}, status_code={waiting_times_result.status_code}]"
            )
            raise WaitingTimeSourceAvailablityException()

        waiting_times_json = waiting_times_result.json()

        result = []
        for office in waiting_times_json:
            internal_office_id = settings.CITY_OFFICE_LOOKUP_TABLE.get(office["id"])
            if internal_office_id is None:
                continue

            waiting_count = office["waiting"]
            waiting_time = office["waittime"]

            city_office = CityOffice.objects.filter(
                identifier=internal_office_id
            ).first()

            if waiting_time.lower() == "meer dan een uur":
                waiting_time = 60
            elif waiting_time.lower() == "geen":
                waiting_time = 0
            else:
                waiting_time = int(waiting_time.split(" ")[0])

            result.append(
                {
                    "title": city_office.title,
                    "identifier": city_office.identifier,
                    "queued": waiting_count,
                    "waitingTime": waiting_time,
                }
            )

        output_serializer = self.get_serializer(
            data={
                "status": True,
                "result": result,
            }
        )
        if not output_serializer.is_valid():
            logger.error(
                f"Waiting time data not in expected format: {output_serializer.errors}"
            )
            raise WaitingTimeDataException()

        return Response(output_serializer.data, status=status.HTTP_200_OK)
