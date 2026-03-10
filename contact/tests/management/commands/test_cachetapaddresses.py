from io import StringIO
from unittest.mock import call, patch

from django.core.management import call_command
from django.test import SimpleTestCase


class TestCacheTapAddressesCommand(SimpleTestCase):
    @patch("contact.management.commands.cachetapaddresses.logger")
    @patch("contact.management.commands.cachetapaddresses.AddressService")
    @patch("contact.management.commands.cachetapaddresses.TapService")
    def test_warms_cache_and_logs_summary(
        self, TapServiceMock, AddressServiceMock, logger_mock
    ):
        taps = [
            {"properties": {"latitude": 52.1, "longitude": 4.1}},
            {"properties": {"latitude": 52.1, "longitude": 4.1}},
            {"properties": {"latitude": 52.2, "longitude": 4.2}},
        ]

        tap_service = TapServiceMock.return_value
        tap_service.get_geojson_items.return_value = [{"raw": "data"}]
        tap_service.filter_data.return_value = taps

        address_service = AddressServiceMock.return_value
        address_service.get_address_by_coordinates.side_effect = [
            {"street": "Damrak"},
            {"street": "Damrak"},
            None,
        ]

        stdout = StringIO()
        call_command("cachetapaddresses", stdout=stdout)

        tap_service.get_geojson_items.assert_called_once_with()
        tap_service.filter_data.assert_called_once_with(
            tap_service.get_geojson_items.return_value
        )

        self.assertEqual(
            address_service.get_address_by_coordinates.call_args_list,
            [
                call(latitude=52.1, longitude=4.1),
                call(latitude=52.1, longitude=4.1),
                call(latitude=52.2, longitude=4.2),
            ],
        )

        summary_messages = [
            c.args[0]
            for c in logger_mock.info.call_args_list
            if c.args
            and isinstance(c.args[0], str)
            and c.args[0].startswith("Cache warm complete:")
        ]
        self.assertEqual(len(summary_messages), 1)
        summary = summary_messages[0]
        self.assertIn("taps=3", summary)
        self.assertIn("unique_coordinates=2", summary)
        self.assertIn("addresses_found=2", summary)
        self.assertIn("addresses_missing=1", summary)

    @patch("contact.management.commands.cachetapaddresses.logger")
    @patch("contact.management.commands.cachetapaddresses.AddressService")
    @patch("contact.management.commands.cachetapaddresses.TapService")
    def test_handles_missing_properties(
        self, TapServiceMock, AddressServiceMock, logger_mock
    ):
        taps = [
            {},
            {"properties": None},
            {"properties": {"latitude": 52.3, "longitude": 4.3}},
        ]

        tap_service = TapServiceMock.return_value
        tap_service.get_geojson_items.return_value = []
        tap_service.filter_data.return_value = taps

        address_service = AddressServiceMock.return_value
        address_service.get_address_by_coordinates.side_effect = [
            None,
            None,
            {"ok": True},
        ]

        call_command("cachetapaddresses")

        self.assertEqual(
            address_service.get_address_by_coordinates.call_args_list,
            [
                call(latitude=None, longitude=None),
                call(latitude=None, longitude=None),
                call(latitude=52.3, longitude=4.3),
            ],
        )

        summary_messages = [
            c.args[0]
            for c in logger_mock.info.call_args_list
            if c.args
            and isinstance(c.args[0], str)
            and c.args[0].startswith("Cache warm complete:")
        ]
        self.assertEqual(len(summary_messages), 1)
        summary = summary_messages[0]
        self.assertIn("taps=3", summary)
        self.assertIn("addresses_found=1", summary)
        self.assertIn("addresses_missing=2", summary)
