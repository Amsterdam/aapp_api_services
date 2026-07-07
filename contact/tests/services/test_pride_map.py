from unittest.mock import patch

from django.test import SimpleTestCase

from contact.services.pride_map import PrideMapService


class PrideMapServiceTest(SimpleTestCase):
    def setUp(self):
        self.service = PrideMapService()

    def test_preprocess_feature_multipoint_to_point(self):
        feature = {
            "geometry": {
                "type": "MultiPoint",
                "coordinates": [[4.89, 52.37], [4.9, 52.38]],
            },
            "properties": {"id": "x"},
        }

        self.service._preprocess_feature(
            feature=feature,
            layer={"label": "Evenement"},
        )

        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertEqual(feature["geometry"]["coordinates"], [4.89, 52.37])

    def test_preprocess_feature_keeps_geometry(self):
        feature = {
            "geometry": {"type": "Point", "coordinates": [4.89, 52.37]},
            "properties": {"id": "x"},
        }

        self.service._preprocess_feature(
            feature=feature,
            layer={"label": "Evenement"},
        )

        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertEqual(feature["geometry"]["coordinates"], [4.89, 52.37])

    def test_get_custom_properties_default_layer(self):
        properties = {
            "title": "Event",
            "description": "<p>Desc</p>",
            "street": "Damrak",
            "street_number": "1",
            "zip": "1012LG",
            "city": "Amsterdam",
            "website": "https:\\/\\/example.org",
            "meta": [{"title": "Type", "value": "Muziek"}],
        }
        geom = {"type": "Point", "coordinates": [4.9, 52.3]}

        custom = self.service.get_custom_properties(
            properties=properties,
            geom=geom,
            layer_type="Evenement",
            icon_name="event",
        )

        self.assertEqual(custom["aapp_title"], "Event")
        self.assertEqual(custom["aapp_subtitle"], "Evenement")
        self.assertEqual(custom["aapp_date_and_time"], None)
        self.assertEqual(custom["aapp_website"], "https://example.org")
        self.assertEqual(custom["aapp_address"]["coordinates"]["lat"], 52.3)
        self.assertEqual(custom["aapp_address"]["coordinates"]["lon"], 4.9)
        self.assertEqual(custom["aapp_table"], [{"key": "Type", "value": "Muziek"}])
        self.assertEqual(custom["stroke"], None)

    def test_get_custom_properties_canal_parade_linestring_stroke(self):
        custom = self.service.get_custom_properties(
            properties={"title": "Parade"},
            geom={"type": "LineString", "coordinates": [[4.9, 52.3], [4.91, 52.31]]},
            layer_type="Canal parade",
            icon_name="canal_parade",
        )

        self.assertEqual(custom["stroke"], "#009DE6")
        self.assertEqual(custom["stroke-width"], 5)

    def test_get_custom_properties_without_street_has_no_address(self):
        custom = self.service.get_custom_properties(
            properties={"title": "No street", "meta": []},
            geom={"type": "Point", "coordinates": [4.9, 52.3]},
            layer_type="Evenement",
            icon_name="event",
        )

        self.assertEqual(custom["aapp_address"], None)
        self.assertEqual(custom["aapp_table"], None)

    def test_get_custom_properties_toilet_uses_generated_description(self):
        custom = self.service.get_custom_properties(
            properties={
                "title": "Toilet West",
                "date_start": "2026-08-01T06:00:00+02:00",
                "date_end": "2026-08-01T23:30:00+02:00",
                "meta": [],
            },
            geom={"type": "Point", "coordinates": [4.9, 52.3]},
            layer_type="Toilet",
            icon_name="toilet",
        )

        self.assertEqual(
            custom["aapp_date_and_time"],
            "za 1 aug 2026, 06:00 tot 23:30",
        )
        self.assertEqual(custom["aapp_start_date"], "2026-08-01")
        self.assertEqual(custom["aapp_end_date"], "2026-08-01")
        self.assertEqual(custom["aapp_start_time"], "06:00:00")
        self.assertEqual(custom["aapp_end_time"], "23:30:00")

    def test_get_date_and_time_for_toilets_handles_date_range_and_end_only_time(self):
        date_and_time = self.service._get_date_and_time_for_toilets(
            {
                "date_start": "2026-08-01",
                "date_end": "2026-08-02T23:30:00+02:00",
            }
        )

        self.assertEqual(date_and_time, "za 1 aug 2026 - zo 2 aug 2026, tot 23:30")

    def test_get_date_and_time_for_toilets_handles_start_only_time(self):
        date_and_time = self.service._get_date_and_time_for_toilets(
            {
                "date_start": "2026-08-01T06:00:00+02:00",
                "date_end": "2026-08-01",
            }
        )

        self.assertEqual(date_and_time, "za 1 aug 2026, vanaf 06:00")

    def test_get_date_and_time_for_toilets_handles_no_times(self):
        date_and_time = self.service._get_date_and_time_for_toilets(
            {
                "date_start": "2026-08-01",
                "date_end": "2026-08-02",
            }
        )

        self.assertEqual(date_and_time, "za 1 aug 2026 - zo 2 aug 2026")

    def test_get_date_and_time_from_description(self):
        custom = self.service.get_custom_properties(
            properties={
                "id": "13073709",
                "title": "Pride Walk",
                "description": "<p>za 1 aug 2026, 11:00 tot 15:00<\/p>",
                "meta": [
                    {
                        "key": "type",
                        "title": "Type",
                        "value": "pride-walk",
                        "presenter": "text",
                    }
                ],
            },
            geom={"type": "LineString", "coordinates": [[4.9, 52.3], [4.91, 52.31]]},
            layer_type="Pride walk",
            icon_name="pride_walk",
        )
        self.assertEqual(
            custom["aapp_date_and_time"],
            "za 1 aug 2026, 11:00 tot 15:00",
        )

    def test_get_date_and_time_from_meta(self):
        custom = self.service.get_custom_properties(
            properties={
                "id": "13073709",
                "title": "Pride Walk",
                "meta": [
                    {"key": "startdatum", "value": "8-jul"},
                    {"key": "datum-eind-tm", "value": "2026-07-09 extra"},
                    {"key": "tijd", "value": "06.00 - 23.30"},
                ],
            },
            geom={"type": "LineString", "coordinates": [[4.9, 52.3], [4.91, 52.31]]},
            layer_type="Pride walk",
            icon_name="pride_walk",
        )
        self.assertEqual(
            custom["aapp_date_and_time"],
            "wo 8 jul 2026 - do 9 jul 2026, 06:00 tot 23:30",
        )

    def test_get_date_and_time_from_meta_unspecified_time(self):
        custom = self.service.get_custom_properties(
            properties={
                "id": "13073709",
                "title": "Pride Walk",
                "meta": [
                    {"key": "datum-start", "value": "8-jul"},
                    {"key": "datum-eind", "value": "2026-07-09 extra"},
                    {"key": "tijd", "value": "doorlopend"},
                ],
            },
            geom={"type": "LineString", "coordinates": [[4.9, 52.3], [4.91, 52.31]]},
            layer_type="Pride walk",
            icon_name="pride_walk",
        )
        self.assertEqual(
            custom["aapp_date_and_time"],
            "wo 8 jul 2026 - do 9 jul 2026",
        )

    def test_get_start_end_date_and_time_reads_meta_dates_and_time_range(self):
        with patch("contact.services.pride_map.datetime") as mock_datetime:
            mock_datetime.now.return_value.year = 2026
            mock_datetime.strptime.side_effect = lambda *args, **kwargs: __import__(
                "datetime"
            ).datetime.strptime(*args, **kwargs)

            date_properties = self.service._get_start_end_date_and_time(
                {
                    "meta": [
                        {"key": "startdatum", "value": "8-jul"},
                        {"key": "datum-eind-tm", "value": "2026-07-09 extra"},
                        {"key": "tijd", "value": "06.00 - 23.30"},
                    ]
                }
            )

        self.assertEqual(
            date_properties,
            {
                "start_date": "2026-07-08",
                "end_date": "2026-07-09",
                "start_time": "06:00",
                "end_time": "23:30",
            },
        )

    def test_get_start_end_date_and_time_skips_unexpected_meta_time_format(self):
        with patch("contact.services.pride_map.logger.warning") as warning:
            date_properties = self.service._get_start_end_date_and_time(
                {
                    "meta": [
                        {"key": "datum-start", "value": "2026-07-08"},
                        {"key": "einddatum", "value": "2026-07-09"},
                        {"key": "tijd", "value": "06:00-23:30-extra"},
                    ]
                }
            )

        self.assertEqual(date_properties["start_date"], "2026-07-08")
        self.assertEqual(date_properties["end_date"], "2026-07-09")
        self.assertEqual(date_properties["start_time"], None)
        self.assertEqual(date_properties["end_time"], None)
        warning.assert_called_once()

    def test_get_start_end_date_and_time_skips_meta_time_without_range(self):
        date_properties = self.service._get_start_end_date_and_time(
            {
                "meta": [
                    {"key": "startdatum", "value": "2026-07-08"},
                    {"key": "tijd", "value": "06:00"},
                ]
            }
        )

        self.assertEqual(date_properties["start_date"], "2026-07-08")
        self.assertEqual(date_properties["start_time"], None)
        self.assertEqual(date_properties["end_time"], None)

    def test_convert_date_string_to_iso_format_returns_iso_or_none(self):
        self.assertEqual(
            self.service._convert_date_string_to_iso_format("2026-07-08 garbage"),
            "2026-07-08",
        )
        self.assertIsNone(self.service._convert_date_string_to_iso_format(None))

    def test_convert_date_string_to_iso_format_converts_short_month(self):
        with patch("contact.services.pride_map.datetime") as mock_datetime:
            mock_datetime.now.return_value.year = 2026
            mock_datetime.strptime.side_effect = lambda *args, **kwargs: __import__(
                "datetime"
            ).datetime.strptime(*args, **kwargs)

            value = self.service._convert_date_string_to_iso_format("8-jul")

        self.assertEqual(value, "2026-07-08")

    def test_convert_date_string_to_iso_format_logs_invalid_short_month(self):
        with patch("contact.services.pride_map.datetime") as mock_datetime:
            mock_datetime.now.return_value.year = 2026
            mock_datetime.strptime.side_effect = ValueError

            with patch("contact.services.pride_map.logger.warning") as warning:
                value = self.service._convert_date_string_to_iso_format("8-xyz")

        self.assertIsNone(value)
        warning.assert_called_once_with("Could not convert date string: 8-xyz-2026")

    def test_convert_date_string_to_iso_format_returns_none_for_unknown_format(self):
        self.assertIsNone(
            self.service._convert_date_string_to_iso_format("not-a-supported-date")
        )
