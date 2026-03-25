import datetime

from django.test import TestCase
from model_bakery import baker

from waste.interpret_frequencies import interpret_frequencies
from waste.models import WasteCollectionException


class InterpretFrequenciesExceptionDatesTest(TestCase):
    def setUp(self):
        self.dates = [datetime.date(2026, 1, day + 1) for day in range(7)]
        self.ophaaldagen_list = [0, 1, 2, 3, 4, 5, 6]

    def test_no_exception_dates(self):
        interpreted_dates = interpret_frequencies(
            dates=self.dates,
            ophaaldagen_list=self.ophaaldagen_list,
        )
        self.assertEqual(interpreted_dates, self.dates)

    def test_single_exception_dates(self):
        baker.make(WasteCollectionException, date=self.dates[0])

        interpreted_dates = interpret_frequencies(
            dates=self.dates,
            ophaaldagen_list=self.ophaaldagen_list,
        )
        self.assertEqual(interpreted_dates, self.dates[1:])

    def test_multiple_exception_dates(self):
        baker.make(WasteCollectionException, date=self.dates[0])
        baker.make(WasteCollectionException, date=self.dates[1])

        interpreted_dates = interpret_frequencies(
            dates=self.dates,
            ophaaldagen_list=self.ophaaldagen_list,
        )
        self.assertEqual(interpreted_dates, self.dates[2:])

    def test_all_exception_dates(self):
        for d in self.dates:
            baker.make(WasteCollectionException, date=d)

        interpreted_dates = interpret_frequencies(
            dates=self.dates,
            ophaaldagen_list=self.ophaaldagen_list,
        )
        self.assertEqual(interpreted_dates, [])
