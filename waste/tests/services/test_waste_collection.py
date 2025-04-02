from datetime import date, datetime
from unittest.mock import patch

import freezegun
from django.test import TestCase, override_settings

from waste.services.waste_collection import WasteCollectionService


@freezegun.freeze_time("2025-03-27")
@patch("waste.services.waste_collection.requests.get")
class WasteCollectionServiceTest(TestCase):
    def setUp(self):
        self.service = WasteCollectionService(bag_nummeraanduiding_id="1234")

    def test_get_validated_data(self, mock_request_get):
        self.get_validated_mock_data(mock_request_get)
        self.assertIsNotNone(self.service.validated_data)

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_calendar(self, mock_request_get):
        self.get_validated_mock_data(mock_request_get)
        calendar = self.service.create_calendar()

        self.assertEqual(
            calendar,
            [
                {
                    "date": date(year=2025, month=3, day=31),
                    "label": "Papier",
                    "type": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "note": "Geen melding",
                },
                {
                    "date": date(year=2025, month=4, day=1),
                    "label": "Groente fruit en tuin",
                    "type": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "note": "Test melding",
                },
                {
                    "date": date(year=2025, month=4, day=7),
                    "label": "Papier",
                    "type": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "note": "Geen melding",
                },
                {
                    "date": date(year=2025, month=4, day=8),
                    "label": "Groente fruit en tuin",
                    "type": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "note": "Test melding",
                },
            ],
        )

    def test_get_next_dates(self, mock_request_get):
        self.get_validated_mock_data(mock_request_get)
        calendar = self.service.create_calendar()
        next_dates = self.service.get_next_dates(calendar)

        self.assertEqual(
            next_dates,
            {
                "Papier": date(year=2025, month=3, day=31),
                "GFT": date(year=2025, month=4, day=1),
                "Glas": None,
                "Plastic": None,
                "GA": None,
                "Rest": None,
                "Textiel": None,
            },
        )

    def test_get_types(self, mock_request_get):
        self.get_validated_mock_data(mock_request_get)
        calendar = self.service.create_calendar()
        next_dates = self.service.get_next_dates(calendar)
        waste_types = self.service.get_waste_types(next_dates)

        self.assertEqual(
            waste_types,
            [
                {
                    "label": "Papier",
                    "type": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "note": "Geen melding",
                    "remark": "Met hetzelfde gemak",
                    "instruction": "Gooi het in de bak",
                    "next_date": date(year=2025, month=3, day=31),
                },
                {
                    "label": "Groente fruit en tuin",
                    "type": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "note": "Test melding",
                    "remark": "Met hetzelfde gemak",
                    "instruction": "Gooi het in de bak",
                    "next_date": date(year=2025, month=4, day=1),
                },
            ],
        )

    def get_validated_mock_data(self, mock_request_get):
        mock_request_get.return_value.status_code = 200
        mock_request_get.return_value.json.return_value = {
            "_embedded": {
                "afvalwijzer": [
                    {
                        "afvalwijzerOphaaldagen": "maandag",
                        "afvalwijzerFractieNaam": "Papier",
                        "afvalwijzerFractieCode": "Papier",
                        "afvalwijzerBuitenzettenVanaf": "21:00",
                        "afvalwijzerBuitenzettenTot": "7:00",
                        "afvalwijzerAfvalkalenderMelding": "Geen melding",
                        "afvalwijzerAfvalkalenderOpmerking": "Met hetzelfde gemak",
                        "afvalwijzerInstructie2": "Gooi het in de bak",
                        "afvalwijzerAfvalkalenderFrequentie": "null",
                    },
                    {
                        "afvalwijzerOphaaldagen": "dinsdag",
                        "afvalwijzerFractieNaam": "Groente fruit en tuin",
                        "afvalwijzerFractieCode": "GFT",
                        "afvalwijzerBuitenzettenVanaf": "22:00",
                        "afvalwijzerBuitenzettenTot": "7:00",
                        "afvalwijzerAfvalkalenderMelding": "Test melding",
                        "afvalwijzerAfvalkalenderOpmerking": "Met hetzelfde gemak",
                        "afvalwijzerInstructie2": "Gooi het in de bak",
                        "afvalwijzerAfvalkalenderFrequentie": "null",
                    },
                ]
            }
        }
        self.service.get_validated_data()

    @override_settings(CALENDAR_LENGTH=20)
    def test_calendar_even_oneven_weesp(self, mock_request_get):
        mock_request_get.return_value.status_code = 200
        mock_request_get.return_value.json.return_value = {
            "_embedded": {
                "afvalwijzer": [
                    {
                        "afvalwijzerOphaaldagen": "maandag",
                        "afvalwijzerFractieNaam": "Papier",
                        "afvalwijzerFractieCode": "Papier",
                        "afvalwijzerBuitenzettenVanaf": "21:00",
                        "afvalwijzerBuitenzettenTot": "7:00",
                        "afvalwijzerAfvalkalenderMelding": "Geen melding",
                        "afvalwijzerAfvalkalenderOpmerking": "Met hetzelfde gemak",
                        "afvalwijzerInstructie2": "Gooi het in de bak",
                        "afvalwijzerAfvalkalenderFrequentie": "oneven week",
                    },
                    {
                        "afvalwijzerOphaaldagen": "dinsdag",
                        "afvalwijzerFractieNaam": "Groente fruit en tuin",
                        "afvalwijzerFractieCode": "GFT",
                        "afvalwijzerBuitenzettenVanaf": "22:00",
                        "afvalwijzerBuitenzettenTot": "7:00",
                        "afvalwijzerAfvalkalenderMelding": "Test melding",
                        "afvalwijzerAfvalkalenderOpmerking": "Met hetzelfde gemak",
                        "afvalwijzerInstructie2": "Gooi het in de bak",
                        "afvalwijzerAfvalkalenderFrequentie": "even week",
                    },
                ]
            }
        }
        self.service.get_validated_data()
        calendar = self.service.create_calendar()

        self.assertEqual(
            calendar,
            [
                {
                    "date": date(year=2025, month=4, day=1),
                    "label": "Groente fruit en tuin",
                    "type": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "note": "Test melding",
                },
                {
                    "date": date(year=2025, month=4, day=7),
                    "label": "Papier",
                    "type": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "note": "Geen melding",
                },
                {
                    "date": date(year=2025, month=4, day=15),
                    "label": "Groente fruit en tuin",
                    "type": "GFT",
                    "curb_rules_from": "22:00",
                    "curb_rules_to": "7:00",
                    "note": "Test melding",
                },
            ],
        )

    @override_settings(CALENDAR_LENGTH=150)
    def test_calendar_specific_dates_weesp(self, mock_request_get):
        mock_request_get.return_value.status_code = 200
        mock_request_get.return_value.json.return_value = {
            "_embedded": {
                "afvalwijzer": [
                    {
                        "afvalwijzerOphaaldagen": "vrijdag",
                        "afvalwijzerFractieNaam": "Papier",
                        "afvalwijzerFractieCode": "Papier",
                        "afvalwijzerBuitenzettenVanaf": "21:00",
                        "afvalwijzerBuitenzettenTot": "7:00",
                        "afvalwijzerAfvalkalenderMelding": "Geen melding",
                        "afvalwijzerAfvalkalenderOpmerking": "Met hetzelfde gemak",
                        "afvalwijzerInstructie2": "Gooi het in de bak",
                        "afvalwijzerAfvalkalenderFrequentie": "10-1-25 / 7-2-25 / 7-3-25 / 4-4-25 / 2-5-25 / 30-5-25 / 27-6-25 25-7-25 / 22-8-25 / 19-9-25 / 17-10-25 / 14-11-25 / 12-12-25",
                    },
                ]
            }
        }
        self.service.get_validated_data()
        calendar = self.service.create_calendar()

        # interpret date string as datetime
        self.assertEqual(
            calendar,
            [
                {
                    "date": datetime.strptime(d, "%Y-%m-%d").date(),
                    "label": "Papier",
                    "type": "Papier",
                    "curb_rules_from": "21:00",
                    "curb_rules_to": "7:00",
                    "note": "Geen melding",
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
