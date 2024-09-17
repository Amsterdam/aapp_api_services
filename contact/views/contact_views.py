import logging

import requests
from rest_framework import generics, status
from rest_framework.response import Response

from contact.exceptions import CityOfficeDataException
from contact.models import CityOffice, OpeningHours, OpeningHoursException
from contact.serializers.contact_serializers import CityOfficeResultSerializer

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


def waiting_times(request):
    """
    Redirect call to Amsterdam "wachtijden" API.
    Enrich result with city office names.
    """
    WAITING_TIME_API = "https://wachttijdenamsterdam.nl/data/"

    CITY_OFFICE_LOOKUP_TABLE = {
        5: "e9871a7716da02a4c20cfb06f9547005",  # Centrum
        6: "5d9637689a8b902fa1a13acdf0006d26",  # Nieuw-West
        7: "081d6a38f46686905693fcd6087039f5",  # Noord
        8: "29e3b63d09d1f0c9a9c7238064c70790",  # Oost
        9: "b4b178107cbc0c609d8d190bbdbdfb08",  # West
        10: "b887a4d081821c4245c02f07e2de3290",  # Zuid
        11: "d338d28f8e6132ea2cfcf3e61785454c",  # Zuidoost
    }

    not_available_result = {
        "message": "Waiting times API not available",
        "api": WAITING_TIME_API,
        "error": None,
    }

    try:
        waiting_times_result = requests.get(WAITING_TIME_API, timeout=10)
    except requests.exceptions.ConnectionError as e:
        not_available_result["error"] = str(e)
        return Response(
            not_available_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if waiting_times_result.status_code != 200:
        not_available_result[
            "error"
        ] = f"API call returned with status code {waiting_times_result.status_code}"
        return Response(
            not_available_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    waiting_times_json = waiting_times_result.json()

    result = []
    for office in waiting_times_json:
        internal_office_id = CITY_OFFICE_LOOKUP_TABLE.get(office["id"])
        if internal_office_id is None:
            continue

        waiting_count = office["waiting"]
        waiting_time = office["waittime"]

        city_office = CityOffice.objects.filter(identifier=internal_office_id).first()

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

    result_data = {
        "status": True,
        "result": result,
    }
    return Response(result_data, status=status.HTTP_200_OK)
