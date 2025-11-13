import re
from datetime import date, datetime

import freezegun
import responses
from django.conf import settings
from django.test import TestCase, override_settings

from waste.services.waste_collection import WasteCollectionService


@freezegun.freeze_time("2025-03-27")
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
        self.paper_frequency = "null"

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
        self.gft_frequency = "null"

        self.default_waste_guide = [
            {
                "afvalwijzerOphaaldagen2": self.paper_days,
                "afvalwijzerOphaaldagen2Array": self.paper_days_array,
                "afvalwijzerFractieNaam": self.paper_label,
                "afvalwijzerFractieCode": self.paper_code,
                "afvalwijzerBuitenzetten": self.paper_curb_rules,
                "afvalwijzerBuitenzettenVanaf": self.paper_curb_rules_from,
                "afvalwijzerBuitenzettenTot": self.paper_curb_rules_to,
                "afvalwijzerAfvalkalenderMelding": self.paper_alert,
                "afvalwijzerAfvalkalenderOpmerking": self.paper_note,
                "afvalwijzerInstructie2": self.paper_how,
                "afvalwijzerAfvalkalenderFrequentie": "null",
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
                "afvalwijzerFractieCode": self.gft_code,
                "afvalwijzerBuitenzetten": self.gft_curb_rules,
                "afvalwijzerBuitenzettenVanaf": self.gft_curb_rules_from,
                "afvalwijzerBuitenzettenTot": self.gft_curb_rules_to,
                "afvalwijzerAfvalkalenderMelding": self.gft_alert,
                "afvalwijzerAfvalkalenderOpmerking": self.gft_note,
                "afvalwijzerInstructie2": self.gft_how,
                "afvalwijzerAfvalkalenderFrequentie": "null",
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

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_calendar(self):
        self.set_validated_mock_data(self.default_waste_guide)
        calendar = self.service.create_calendar()

        self.assertEqual(
            calendar,
            [
                {
                    "date": date(year=2025, month=3, day=31),
                    "label": self.paper_label,
                    "code": self.paper_code,
                    "curb_rules_from": self.paper_curb_rules_from,
                    "curb_rules_to": self.paper_curb_rules_to,
                    "alert": self.paper_alert,
                },
                {
                    "date": date(year=2025, month=4, day=1),
                    "label": self.gft_label,
                    "code": self.gft_code,
                    "curb_rules_from": self.gft_curb_rules_from,
                    "curb_rules_to": self.gft_curb_rules_to,
                    "alert": self.gft_alert,
                },
                {
                    "date": date(year=2025, month=4, day=7),
                    "label": self.paper_label,
                    "code": self.paper_code,
                    "curb_rules_from": self.paper_curb_rules_from,
                    "curb_rules_to": self.paper_curb_rules_to,
                    "alert": self.paper_alert,
                },
                {
                    "date": date(year=2025, month=4, day=8),
                    "label": self.gft_label,
                    "code": self.gft_code,
                    "curb_rules_from": self.gft_curb_rules_from,
                    "curb_rules_to": self.gft_curb_rules_to,
                    "alert": self.gft_alert,
                },
            ],
        )

    def test_get_next_dates(self):
        self.set_validated_mock_data(self.default_waste_guide)
        calendar = self.service.create_calendar()
        next_dates = self.service.get_next_dates(calendar)

        self.assertDictEqual(
            next_dates,
            {
                "Papier": date(year=2025, month=3, day=31),
                "GFT": date(year=2025, month=4, day=1),
                "GFET": None,
                "Glas": None,
                "Plastic": None,
                "GA": None,
                "Rest": None,
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
                    "label": self.paper_label,
                    "code": self.paper_code,
                    "curb_rules": self.paper_curb_rules,
                    "alert": self.paper_alert,
                    "note": self.paper_note,
                    "days_array": self.paper_days_array,
                    "how": self.paper_how,
                    "where": self.paper_where,
                    "button_text": self.paper_button_text,
                    "url": self.paper_url,
                    "frequency": self.paper_frequency,
                    "next_date": date(year=2025, month=3, day=31),
                    "is_collection_by_appointment": False,
                },
                {
                    "label": self.gft_label,
                    "code": self.gft_code,
                    "curb_rules": self.gft_curb_rules,
                    "alert": self.gft_alert,
                    "note": self.gft_note,
                    "days_array": self.gft_days_array,
                    "how": self.gft_how,
                    "where": self.gft_where,
                    "button_text": self.gft_button_text,
                    "url": self.gft_url,
                    "frequency": self.gft_frequency,
                    "next_date": date(year=2025, month=4, day=1),
                    "is_collection_by_appointment": False,
                },
            ],
        )

    @override_settings(CALENDAR_LENGTH=20)
    def test_calendar_even_oneven_weesp(self):
        waste_guide = [
            {
                "afvalwijzerOphaaldagen2": "maandag",
                "afvalwijzerFractieNaam": self.paper_label,
                "afvalwijzerFractieCode": self.paper_code,
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
                "afvalwijzerFractieCode": self.gft_code,
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
                    "date": date(year=2025, month=4, day=1),
                    "label": self.gft_label,
                    "code": self.gft_code,
                    "curb_rules_from": self.gft_curb_rules_from,
                    "curb_rules_to": self.gft_curb_rules_to,
                    "alert": self.gft_alert,
                },
                {
                    "date": date(year=2025, month=4, day=7),
                    "label": "Papier",
                    "code": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "alert": "Geen melding",
                },
                {
                    "date": date(year=2025, month=4, day=15),
                    "label": "Groente fruit en tuin",
                    "code": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "alert": "Test melding",
                },
            ],
        )

    @override_settings(CALENDAR_LENGTH=150)
    def test_calendar_specific_dates_weesp(self):
        waste_guide = [
            {
                "afvalwijzerOphaaldagen2": "vrijdag",
                "afvalwijzerFractieNaam": self.paper_label,
                "afvalwijzerFractieCode": self.paper_code,
                "afvalwijzerBuitenzetten": self.paper_curb_rules,
                "afvalwijzerBuitenzettenVanaf": self.paper_curb_rules_from,
                "afvalwijzerBuitenzettenTot": self.paper_curb_rules_to,
                "afvalwijzerAfvalkalenderMelding": self.paper_alert,
                "afvalwijzerAfvalkalenderOpmerking": self.paper_note,
                "afvalwijzerInstructie2": self.paper_how,
                "afvalwijzerAfvalkalenderFrequentie": "10-1-25 / 7-2-25 / 7-3-25 / 4-4-25 / 2-5-25 / 30-5-25 / 27-6-25 25-7-25 / 22-8-25 / 19-9-25 / 17-10-25 / 14-11-25 / 12-12-25",
                "afvalwijzerButtontekst": "Test",
                "afvalwijzerUrl": "https://test.nl",
                "afvalwijzerWaar": "Test",
                "gebruiksdoelWoonfunctie": True,
                "afvalwijzerBasisroutetypeCode": "",
            }
        ]
        self.set_validated_mock_data(waste_guide)

        calendar = self.service.create_calendar()

        # interpret date string as datetime
        self.assertEqual(
            calendar,
            [
                {
                    "date": datetime.strptime(d, "%Y-%m-%d").date(),
                    "label": self.paper_label,
                    "code": self.paper_code,
                    "curb_rules_from": self.paper_curb_rules_from,
                    "curb_rules_to": self.paper_curb_rules_to,
                    "alert": self.paper_alert,
                }
                for d in [
                    "2025-04-04",
                    "2025-05-02",
                    "2025-05-30",
                    "2025-06-27",
                    "2025-07-25",
                    "2025-08-22",
                ]
            ],
        )
