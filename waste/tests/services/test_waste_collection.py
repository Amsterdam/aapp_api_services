import re
from datetime import date, datetime

import freezegun
import responses
from django.conf import settings
from django.test import TestCase, override_settings

from waste.services.waste_collection import WasteCollectionService
from waste.tests.mock_data import (
    frequency_four_weeks,
    frequency_hardcoded_with_year,
    frequency_hardcoded_wo_year,
    frequency_monthly,
    frequency_weekly,
    frequency_weekly_oneven,
)


@freezegun.freeze_time("2025-12-09")
class WasteCollectionServiceTest(TestCase):
    @override_settings(CALENDAR_LENGTH=60)
    def setUp(self):
        self.service = WasteCollectionService(bag_nummeraanduiding_id="1234")

    @responses.activate
    def set_validated_mock_data(self, mock_data):
        responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"),
            json=mock_data,
        )
        self.service.get_validated_data()

    def test_create_calendar(self):
        self.set_validated_mock_data(frequency_weekly.MOCK_DATA)
        calendar = self.service.create_calendar()

        self.assertEqual(
            calendar,
            [
                {
                    "date": date(2025, 12, 10),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 10),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 17),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 17),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 24),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 24),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 31),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 31),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 7),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 7),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 14),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 14),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 21),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 21),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 28),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 28),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 2, 4),
                    "label": "Restafval",
                    "code": "Rest",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 2, 4),
                    "label": "Grof afval",
                    "code": "GA",
                    "curb_rules_from": "Dinsdag vanaf 21.00",
                    "curb_rules_to": "tot woensdag 07.00 uur",
                    "alert": None,
                },
            ],
        )

    def test_calendar_even_oneven_weesp(self):
        self.set_validated_mock_data(frequency_weekly_oneven.MOCK_DATA)
        calendar = self.service.create_calendar()

        self.assertEqual(
            calendar,
            [
                {
                    "date": date(2025, 12, 9),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "Maandag vanaf 21.00",
                    "curb_rules_to": "tot dinsdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 15),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Donderdag 21.00",
                    "curb_rules_to": "tot vrijdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 23),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "Maandag vanaf 21.00",
                    "curb_rules_to": "tot dinsdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2025, 12, 29),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Donderdag 21.00",
                    "curb_rules_to": "tot vrijdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 6),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "Maandag vanaf 21.00",
                    "curb_rules_to": "tot dinsdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 12),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Donderdag 21.00",
                    "curb_rules_to": "tot vrijdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 20),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "Maandag vanaf 21.00",
                    "curb_rules_to": "tot dinsdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 1, 26),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Donderdag 21.00",
                    "curb_rules_to": "tot vrijdag 07.00 uur",
                    "alert": None,
                },
                {
                    "date": date(2026, 2, 3),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "Maandag vanaf 21.00",
                    "curb_rules_to": "tot dinsdag 07.00 uur",
                    "alert": None,
                },
            ],
        )

    def test_calendar_specific_dates_weesp(self):
        self.set_validated_mock_data(frequency_hardcoded_wo_year.MOCK_DATA)
        calendar = self.service.create_calendar()

        # interpret date string as datetime
        self.assertEqual(
            calendar,
            [
                {
                    "date": datetime.strptime(d, "%Y-%m-%d").date(),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Donderdag 21.00",
                    "curb_rules_to": "tot vrijdag 07.00 uur",
                    "alert": None,
                }
                for d in [
                    "2025-12-12",
                    "2026-01-09",
                    "2026-02-06",
                ]
            ],
        )

    def test_calendar_specific_dates_weesp_with_year(self):
        self.set_validated_mock_data(frequency_hardcoded_with_year.MOCK_DATA)
        calendar = self.service.create_calendar()

        # interpret date string as datetime
        self.assertEqual(
            calendar,
            [
                {
                    "date": datetime.strptime(d, "%Y-%m-%d").date(),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Donderdag 21.00",
                    "curb_rules_to": "tot vrijdag 07.00 uur",
                    "alert": None,
                }
                for d in [
                    "2025-12-12",
                    "2026-01-09",
                    "2026-02-06",
                ]
            ],
        )

    def test_calendar_montly_frequency_success(self):
        self.set_validated_mock_data(frequency_monthly.MOCK_DATA)
        calendar = self.service.create_calendar()

        # interpret date string as datetime
        self.assertEqual(
            calendar,
            [
                {
                    "date": date(2026, 1, 12),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Zondag vanaf 21.00",
                    "curb_rules_to": "tot maandag 07.00 uur",
                    "alert": None,
                }
            ],
        )

    def test_calendar_four_weeks(self):
        self.set_validated_mock_data(frequency_four_weeks.MOCK_DATA)
        calendar = self.service.create_calendar()

        # interpret date string as datetime
        self.assertEqual(
            calendar,
            [
                {
                    "date": date(2026, 1, 23),
                    "label": "Papier en karton",
                    "code": "Papier",
                    "curb_rules_from": "Donderdag vanaf 21.00",
                    "curb_rules_to": "tot vrijdag 07.00 uur",
                    "alert": None,
                }
            ],
        )

    def test_get_next_dates(self):
        self.set_validated_mock_data(frequency_weekly.MOCK_DATA)
        calendar = self.service.create_calendar()
        next_dates = self.service.get_next_dates(calendar)

        self.assertDictEqual(
            next_dates,
            {
                "Rest": date(2025, 12, 10),
                "GA": date(2025, 12, 10),
                "Papier": None,
                "GFT": None,
                "Glas": None,
                "Textiel": None,
            },
        )

    def test_get_waste_types(self):
        self.set_validated_mock_data(frequency_weekly.MOCK_DATA)
        calendar = self.service.create_calendar()
        next_dates = self.service.get_next_dates(calendar)
        waste_types = self.service.get_waste_types(next_dates)

        self.assertEqual(
            waste_types,
            [
                {
                    "label": "Restafval",
                    "code": "Rest",
                    "order": 1,
                    "curb_rules": "Dinsdag vanaf 21.00 tot woensdag 07.00 uur",
                    "alert": None,
                    "note": None,
                    "days_array": ["woensdag"],
                    "how": "In rolcontainer",
                    "where": "Aan de rand van de stoep of op de vaste plek",
                    "button_text": None,
                    "url": None,
                    "frequency": None,
                    "is_collection_by_appointment": False,
                    "next_date": date(2025, 12, 10),
                    "info_link": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/restafval/",
                },
                {
                    "label": "Grof afval",
                    "code": "GA",
                    "order": 3,
                    "curb_rules": "Dinsdag vanaf 21.00 tot woensdag 07.00 uur",
                    "alert": None,
                    "note": None,
                    "days_array": ["woensdag"],
                    "how": "Breng uw grof afval naar een Recyclepunt of buiten zetten",
                    "where": "Aan de rand van de stoep of op de vaste plek",
                    "button_text": None,
                    "url": "https://kaart.amsterdam.nl/recyclepunten",
                    "frequency": None,
                    "is_collection_by_appointment": False,
                    "next_date": date(2025, 12, 10),
                    "info_link": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/grofvuil/",
                },
            ],
        )

    def test_sort_waste_types_by_order(self):
        waste_types = [
            {"code": "GFT", "order": 3},
            {"code": "Rest", "order": 1},
            {"code": "Papier", "order": 2},
            {"code": "Glas", "order": None},
        ]

        sorted_waste_types = self.service.sort_waste_types_by_order(waste_types)

        self.assertEqual(
            sorted_waste_types,
            [
                {"code": "Rest", "order": 1},
                {"code": "Papier", "order": 2},
                {"code": "GFT", "order": 3},
                {"code": "Glas", "order": None},
            ],
        )
