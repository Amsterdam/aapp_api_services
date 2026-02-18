import datetime

from django.test.utils import override_settings
from django.urls import reverse

from contact.models import (
    CityOffice,
    CityOfficeOpeningHours,
    OpeningHoursException,
    RegularOpeningHours,
)
from core.tests.test_authentication import BasicAPITestCase


@override_settings(
    CITY_OFFICE_LOOKUP_TABLE={"1": "stadsloket-centrum"},
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
)
class BaseContactTestCase(BasicAPITestCase):
    def setUp(self):
        super().setUp()

        # Create test data using the provided address
        self.city_office = CityOffice.objects.create(
            identifier="stadsloket-centrum",
            title="Stadsloket Centrum",
            images={"image1": "url1", "image2": "url2"},
            street_name="Amstel",
            street_number="1",
            postal_code="1011 PN",
            city="Amsterdam",
            lat=52.3676,
            lon=4.9041,
            directions_url="http://example.com/directions",
            appointment={"type": "appointment_info"},
            visiting_hours_content="Visit us between 9am and 5pm.",
            address_content={"additional": "info"},
            order=0,
        )

        self.city_office_opening_hours = CityOfficeOpeningHours.objects.create(
            city_office=self.city_office,
        )

        # Create OpeningHours for the city office
        RegularOpeningHours.objects.create(
            city_office_opening_hours=self.city_office_opening_hours,
            day_of_week=1,  # Monday
            opens_time="09:00",
            closes_time="17:00",
        )

        # Create an OpeningHoursException for the city office
        exception = OpeningHoursException.objects.create(
            date=datetime.date.today(),
            opens_time="10:00",
            closes_time="16:00",
            description="Test exception",
        )
        exception.affected_offices.add(self.city_office)


class TestCityOfficeView(BaseContactTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("contact-city-offices")

    def test_get_city_offices(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Check that the status is True
        self.assertTrue(response_data.get("status"))

        # Check that result contains the correct data
        result = response_data.get("result")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        office_data = result[0]
        self.assertEqual(office_data["identifier"], "stadsloket-centrum")
        self.assertEqual(office_data["title"], "Stadsloket Centrum")
        self.assertEqual(office_data["image"], {"image1": "url1", "image2": "url2"})
        self.assertEqual(office_data["address"]["streetName"], "Amstel")
        self.assertEqual(office_data["address"]["streetNumber"], "1")
        self.assertEqual(office_data["address"]["postalCode"], "1011 PN")
        self.assertEqual(office_data["address"]["city"], "Amsterdam")
        self.assertEqual(office_data["coordinates"]["lat"], 52.3676)
        self.assertEqual(office_data["coordinates"]["lon"], 4.9041)
        self.assertEqual(office_data["directionsUrl"], "http://example.com/directions")
        self.assertEqual(office_data["appointment"], {"type": "appointment_info"})
        self.assertEqual(
            office_data["visitingHoursContent"], "Visit us between 9am and 5pm."
        )
        self.assertEqual(office_data["addressContent"], {"additional": "info"})
        self.assertEqual(office_data["order"], 0)

        # Check visiting hours
        visiting_hours = office_data["visitingHours"]
        self.assertIn("regular", visiting_hours)
        self.assertIn("exceptions", visiting_hours)

        # Check regular opening hours
        regular_hours = visiting_hours["regular"]
        self.assertIsInstance(regular_hours, list)
        self.assertEqual(len(regular_hours), 1)
        regular_hour = regular_hours[0]
        self.assertEqual(regular_hour["dayOfWeek"], 1)
        self.assertEqual(regular_hour["opening"], {"hours": 9, "minutes": 0})
        self.assertEqual(regular_hour["closing"], {"hours": 17, "minutes": 0})

        # Check exception opening hours
        exceptions = visiting_hours["exceptions"]
        self.assertIsInstance(exceptions, list)
        self.assertEqual(len(exceptions), 1)
        exception = exceptions[0]
        self.assertEqual(exception["date"], datetime.date.today().isoformat())
        self.assertEqual(exception["opening"], {"hours": 10, "minutes": 0})
        self.assertEqual(exception["closing"], {"hours": 16, "minutes": 0})
        self.assertEqual(exception["description"], "Test exception")

    def test_get_city_offices_empty(self):
        # Remove existing data
        CityOffice.objects.all().delete()

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Check that the status is True
        self.assertTrue(response_data.get("status"))

        # Check that result is an empty list
        result = response_data.get("result")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


class TestHealthCheckView(BasicAPITestCase):
    def test_health_check_view(self):
        response = self.client.get(
            reverse("contact-health-check"), headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")
