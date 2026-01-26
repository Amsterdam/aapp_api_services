import re
from datetime import date, datetime

import freezegun
import responses
from django.conf import settings
from django.test import TestCase, override_settings
from ics import Calendar

from waste.services.waste_collection import WasteCollectionService
from waste.tests.mock_data import (
    frequency_hardcoded_with_year,
    frequency_hardcoded_wo_year,
    frequency_monthly,
    frequency_unknown,
)


@freezegun.freeze_time("2025-12-09")
class WasteCollectionServiceTest(TestCase):
    def setUp(self):
        self.service = WasteCollectionService(bag_nummeraanduiding_id="1234")

        self.paper_days = "maandag"
        self.paper_days_array = ["maandag"]
        self.paper_label = "Papier"
        self.paper_code = "Papier"
        self.paper_curb_rules = "Van 21:00 tot 07:00"
        self.paper_curb_rules_from = "21:00"
        self.paper_curb_rules_to = "7:00"
        self.paper_alert = "Geen melding"
        self.paper_note = "Met hetzelfde gemak"
        self.paper_how = "Gooi het in de bak"
        self.paper_where = "Straat"
        self.paper_button_text = "Recyclepunt"
        self.paper_url = "https://recyclepunt.nl"
        self.paper_frequency = None

        self.gft_days = "dinsdag"
        self.gft_days_array = ["dinsdag"]
        self.gft_label = "Groente fruit en tuin"
        self.gft_code = "GFT"
        self.gft_curb_rules = "Van 22:00 tot 07:00"
        self.gft_curb_rules_from = "22:00"
        self.gft_curb_rules_to = "7:00"
        self.gft_alert = "Test melding"
        self.gft_note = "Met hetzelfde gemak"
        self.gft_how = "Gooi het in de bak"
        self.gft_where = "Straat"
        self.gft_button_text = "Recyclepunt"
        self.gft_url = "https://recyclepunt.nl"
        self.gft_frequency = None

        self.default_waste_guide = [
            {
                "afvalwijzerOphaaldagen2": self.paper_days,
                "afvalwijzerOphaaldagen2Array": self.paper_days_array,
                "afvalwijzerFractieNaam": self.paper_label,
                "afvalwijzerFractieCode": "Papier",
                "afvalwijzerBuitenzetten": self.paper_curb_rules,
                "afvalwijzerBuitenzettenVanaf": self.paper_curb_rules_from,
                "afvalwijzerBuitenzettenTot": self.paper_curb_rules_to,
                "afvalwijzerAfvalkalenderMelding": self.paper_alert,
                "afvalwijzerAfvalkalenderOpmerking": self.paper_note,
                "afvalwijzerInstructie2": self.paper_how,
                "afvalwijzerAfvalkalenderFrequentie": None,
                "afvalwijzerButtontekst": self.paper_button_text,
                "afvalwijzerUrl": self.paper_url,
                "afvalwijzerWaar": self.paper_where,
                "gebruiksdoelWoonfunctie": True,
                "afvalwijzerBasisroutetypeCode": "",
            },
            {
                "afvalwijzerOphaaldagen2": self.gft_days,
                "afvalwijzerOphaaldagen2Array": self.gft_days_array,
                "afvalwijzerFractieNaam": self.gft_label,
                "afvalwijzerFractieCode": "GFE",
                "afvalwijzerBuitenzetten": self.gft_curb_rules,
                "afvalwijzerBuitenzettenVanaf": self.gft_curb_rules_from,
                "afvalwijzerBuitenzettenTot": self.gft_curb_rules_to,
                "afvalwijzerAfvalkalenderMelding": self.gft_alert,
                "afvalwijzerAfvalkalenderOpmerking": self.gft_note,
                "afvalwijzerInstructie2": self.gft_how,
                "afvalwijzerAfvalkalenderFrequentie": None,
                "afvalwijzerButtontekst": self.gft_button_text,
                "afvalwijzerUrl": self.gft_url,
                "afvalwijzerWaar": self.gft_where,
                "gebruiksdoelWoonfunctie": True,
                "afvalwijzerBasisroutetypeCode": "",
            },
        ]

    @responses.activate
    def set_validated_mock_data(self, waste_guide):
        mocked_response = {"_embedded": {"afvalwijzer": waste_guide}}

        responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"),
            json=mocked_response,
        )
        self.service.get_validated_data()

    def test_get_validated_data(self):
        self.set_validated_mock_data(self.default_waste_guide)
        self.assertIsNotNone(self.service.validated_data)

    def test_get_dates_for_waste_item_unknown_frequency(self):
        item = frequency_unknown.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        dates = self.service._get_dates_for_waste_item(item=item)
        self.assertEqual(len(dates), 0)

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_calendar(self):
        self.set_validated_mock_data(self.default_waste_guide)
        calendar = self.service.create_calendar()

        self.assertEqual(
            calendar,
            [
                {
                    "date": date(2025, 12, 9),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "alert": "Test melding",
                },
                {
                    "date": date(2025, 12, 15),
                    "label": "Papier",
                    "code": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "alert": "Geen melding",
                },
                {
                    "date": date(2025, 12, 16),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "alert": "Test melding",
                },
                {
                    "date": date(2025, 12, 22),
                    "label": "Papier",
                    "code": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "alert": "Geen melding",
                },
            ],
        )

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_ics_calendar(self):
        self.set_validated_mock_data(self.default_waste_guide)
        calendar = self.service.create_ics_calendar()

        self.assertIn("BEGIN:VEVENT", str(calendar))
        self.assertIn("DTSTART:20251214T230000Z", str(calendar))
        # PRODID and DTSTAMP are required for iCalendar standard
        self.assertIn("PRODID", str(calendar))
        self.assertIn("DTSTAMP", str(calendar))
        # SCALE and METHOD are required for Google Calendar standard
        self.assertIn("CALSCALE:GREGORIAN", str(calendar))
        self.assertIn("METHOD:PUBLISH", str(calendar))

    def test_get_next_dates(self):
        self.set_validated_mock_data(self.default_waste_guide)
        calendar = self.service.create_calendar()
        next_dates = self.service.get_next_dates(calendar)

        self.assertDictEqual(
            next_dates,
            {
                "Rest": None,
                "GA": None,
                "Papier": date(2025, 12, 15),
                "GFT": date(2025, 12, 9),
                "Glas": None,
                "Textiel": None,
            },
        )

    def test_get_types(self):
        self.set_validated_mock_data(self.default_waste_guide)
        calendar = self.service.create_calendar()
        next_dates = self.service.get_next_dates(calendar)
        waste_types = self.service.get_waste_types(next_dates)

        self.assertEqual(
            waste_types,
            [
                {
                    "label": "Papier",
                    "code": "Papier",
                    "curb_rules": "Van 21:00 tot 07:00",
                    "alert": "Geen melding",
                    "note": "Met hetzelfde gemak",
                    "days_array": ["maandag"],
                    "how": "Gooi het in de bak",
                    "where": "Straat",
                    "button_text": "Recyclepunt",
                    "url": "https://recyclepunt.nl",
                    "frequency": None,
                    "is_collection_by_appointment": False,
                    "next_date": date(2025, 12, 15),
                    "info_link": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/papier-en-karton/",
                },
                {
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules": "Van 22:00 tot 07:00",
                    "alert": "Test melding",
                    "note": "Met hetzelfde gemak",
                    "days_array": ["dinsdag"],
                    "how": "Gooi het in de bak",
                    "where": "Straat",
                    "button_text": "Recyclepunt",
                    "url": "https://recyclepunt.nl",
                    "frequency": None,
                    "is_collection_by_appointment": False,
                    "next_date": date(2025, 12, 9),
                    "info_link": "https://www.milieucentraal.nl/minder-afval/afval-scheiden/groente-fruit-en-tuinafval-gft/",
                },
            ],
        )

    @override_settings(CALENDAR_LENGTH=20)
    def test_calendar_even_oneven_weesp(self):
        waste_guide = [
            {
                "afvalwijzerOphaaldagen2": "maandag",
                "afvalwijzerFractieNaam": self.paper_label,
                "afvalwijzerFractieCode": "Papier",
                "afvalwijzerBuitenzetten": self.paper_curb_rules,
                "afvalwijzerBuitenzettenVanaf": self.paper_curb_rules_from,
                "afvalwijzerBuitenzettenTot": self.paper_curb_rules_to,
                "afvalwijzerAfvalkalenderMelding": self.paper_alert,
                "afvalwijzerAfvalkalenderOpmerking": self.paper_note,
                "afvalwijzerInstructie2": self.paper_how,
                "afvalwijzerAfvalkalenderFrequentie": "oneven week",
                "afvalwijzerButtontekst": "Test",
                "afvalwijzerUrl": "https://test.nl",
                "afvalwijzerWaar": "Test",
                "gebruiksdoelWoonfunctie": True,
                "afvalwijzerBasisroutetypeCode": "",
            },
            {
                "afvalwijzerOphaaldagen2": "dinsdag",
                "afvalwijzerFractieNaam": self.gft_label,
                "afvalwijzerFractieCode": "GFE",
                "afvalwijzerBuitenzetten": self.gft_curb_rules,
                "afvalwijzerBuitenzettenVanaf": self.gft_curb_rules_from,
                "afvalwijzerBuitenzettenTot": self.gft_curb_rules_to,
                "afvalwijzerAfvalkalenderMelding": self.gft_alert,
                "afvalwijzerAfvalkalenderOpmerking": self.gft_note,
                "afvalwijzerInstructie2": self.gft_how,
                "afvalwijzerAfvalkalenderFrequentie": "even week",
                "afvalwijzerButtontekst": "Test",
                "afvalwijzerUrl": "https://test.nl",
                "afvalwijzerWaar": "Test",
                "gebruiksdoelWoonfunctie": True,
                "afvalwijzerBasisroutetypeCode": "",
            },
        ]
        self.set_validated_mock_data(waste_guide)

        calendar = self.service.create_calendar()
        self.assertEqual(
            calendar,
            [
                {
                    "date": date(2025, 12, 9),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "alert": "Test melding",
                },
                {
                    "date": date(2025, 12, 15),
                    "label": "Papier",
                    "code": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "alert": "Geen melding",
                },
                {
                    "date": date(2025, 12, 23),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "alert": "Test melding",
                },
            ],
        )

    @override_settings(CALENDAR_LENGTH=180)
    def test_calendar_specific_dates_weesp(self):
        self.set_validated_mock_data(
            frequency_hardcoded_wo_year.MOCK_DATA["_embedded"]["afvalwijzer"]
        )
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
                    "2026-03-06",
                    "2026-04-03",
                    "2026-05-01",
                    "2026-05-29",
                ]
            ],
        )

    @override_settings(CALENDAR_LENGTH=380)
    def test_calendar_specific_dates_weesp_with_year(self):
        self.set_validated_mock_data(
            frequency_hardcoded_with_year.MOCK_DATA["_embedded"]["afvalwijzer"]
        )
        calendar = self.service.create_calendar()

        print(f"\n--\n{calendar=}")

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
                    "2026-03-06",
                    "2026-04-03",
                    "2026-05-01",
                    "2026-05-29",
                    "2026-06-26",
                    "2026-07-24",
                    "2026-08-21",
                    "2026-09-18",
                    "2026-10-16",
                    "2026-11-13",
                    "2026-12-11",
                ]
            ],
        )

    @override_settings(CALENDAR_LENGTH=42)
    @responses.activate
    def test_calendar_montly_frequency_success(self):
        self.set_validated_mock_data(
            frequency_monthly.MOCK_DATA["_embedded"]["afvalwijzer"]
        )
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

    @override_settings(CALENDAR_LENGTH=42)
    def test_create_ics_event(self):
        item = frequency_monthly.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        date_object = date(2026, 1, 12)
        event = self.service._create_ics_event(item=item, date=date_object)

        self.assertIn("BEGIN:VEVENT", str(event))
        self.assertIn("DTSTART:20260111T230000Z", str(event))

    @override_settings(CALENDAR_LENGTH=42)
    def test_add_event_to_calendar(self):
        calendar = Calendar()
        item = frequency_monthly.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        date_object = date(2026, 1, 12)

        calendar = self.service._add_event_to_calendar(
            item=item, date=date_object, calendar=calendar
        )

        self.assertIn("BEGIN:VEVENT", str(calendar))
