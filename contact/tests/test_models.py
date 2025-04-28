from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from model_bakery import baker

from contact.models import CityOffice, OpeningHours, OpeningHoursException


class TestCityOfficeModel(TestCase):
    def setUp(self):
        self.obj = baker.make(CityOffice)

    def test_to_string(self):
        self.assertEqual(str(self.obj), self.obj.title)


class TestOpeningHoursModel(TestCase):
    def setUp(self):
        self.city_office = baker.make(CityOffice)
        self.model = OpeningHours

    def test_fully_filled_instance_success(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time="10:00",
            closes_time="18:00",
            day_of_week=1,
        )
        obj.clean()
        obj.save()
        self.assertIsNotNone(obj.id)

    def test_opening_after_closing_not_allowed(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time="18:00",
            closes_time="10:00",
            day_of_week=1,
        )
        with self.assertRaises(ValidationError):
            obj.clean()

    def test_opening_equal_closing_not_allowed(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time="18:00",
            closes_time="18:00",
            day_of_week=1,
        )
        with self.assertRaises(ValidationError):
            obj.clean()

    def test_missing_times(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time=None,
            closes_time=None,
            day_of_week=1,
        )
        with self.assertRaises(IntegrityError):
            obj.save()

    def test_no_opens_time_failed(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time=None,
            closes_time="18:00",
            day_of_week=1,
        )
        with self.assertRaises(IntegrityError):
            obj.save()

    def test_no_closes_time_failed(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time="10:00",
            closes_time=None,
            day_of_week=1,
        )
        with self.assertRaises(IntegrityError):
            obj.save()


class TestOpeningHoursExceptionModel(TestCase):
    def setUp(self):
        self.city_office = baker.make(CityOffice)
        self.model = OpeningHoursException

    def test_fully_filled_instance_success(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time="10:00",
            closes_time="18:00",
            date="2025-01-01",
        )
        obj.save()
        self.assertIsNotNone(obj.id)

    def test_without_times_success(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time=None,
            closes_time=None,
            date="2025-01-01",
        )
        obj.save()
        self.assertIsNotNone(obj.id)

    def test_no_opens_time_failed(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time=None,
            closes_time="18:00",
            date="2025-01-01",
        )
        with self.assertRaises(ValidationError):
            obj.clean()

    def test_no_closes_time_failed(self):
        obj = self.model(
            city_office=self.city_office,
            opens_time="10:00",
            closes_time=None,
            date="2025-01-01",
        )
        with self.assertRaises(ValidationError):
            obj.clean()
