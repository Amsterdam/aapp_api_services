from django.core.management import call_command
from django.test import TestCase

from contact.models import (
    CityOffice,
    CityOfficeOpeningHours,
    RegularOpeningHours,
    WeekDay,
)


class TestInitRegularHoursCommand(TestCase):
    def setUp(self):
        self.city_office = CityOffice.objects.create(
            identifier="test-office",
            title="Test Office",
            images={},
            street_name="Teststraat",
            street_number="1",
            postal_code="1234 AB",
            city="Amsterdam",
            lat=52.0,
            lon=4.0,
            directions_url="",
            appointment={},
            visiting_hours_content="",
            address_content={},
            order=1,
        )

    def test_command_creates_regular_hours(self):
        # No opening hours should exist yet
        self.assertEqual(CityOfficeOpeningHours.objects.count(), 0)
        self.assertEqual(RegularOpeningHours.objects.count(), 0)

        call_command("initregularhours")

        # CityOfficeOpeningHours should be created
        self.assertEqual(CityOfficeOpeningHours.objects.count(), 1)
        opening_hours = CityOfficeOpeningHours.objects.get(city_office=self.city_office)

        # There should be 7 RegularOpeningHours (one for each day)
        regular_hours = RegularOpeningHours.objects.filter(
            city_office_opening_hours=opening_hours
        )
        self.assertEqual(regular_hours.count(), 7)

        # Check that Thursday has closing time 20:00, others 17:00 or None
        thursday = regular_hours.get(day_of_week=WeekDay.THURSDAY)
        self.assertEqual(str(thursday.opens_time), "09:00:00")
        self.assertEqual(str(thursday.closes_time), "20:00:00")
        sunday = regular_hours.get(day_of_week=WeekDay.SUNDAY)
        self.assertIsNone(sunday.opens_time)
        self.assertIsNone(sunday.closes_time)
