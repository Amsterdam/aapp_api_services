from datetime import datetime

from django.test import TestCase, override_settings
from freezegun import freeze_time

from city_pass.utils import get_token_cut_off


class TestUtils(TestCase):
    @override_settings(TOKEN_CUT_OFF_DATETIME="10-1 10:00")
    @freeze_time("2025-01-01 12:00:00+00:00")
    def test_get_datetime_success(self):
        token_cut_off_datetime = get_token_cut_off()
        self.assertEqual(
            token_cut_off_datetime,
            datetime.fromisoformat("2025-10-01 10:00+00:00"),
        )

    @override_settings(TOKEN_CUT_OFF_DATETIME="10-1 10:00")
    @freeze_time("2025-10-01 10:00:00+00:00")
    def test_get_cut_off_moment_equal_to_now(self):
        token_cut_off_datetime = get_token_cut_off()
        self.assertEqual(
            token_cut_off_datetime,
            datetime.fromisoformat("2025-10-01 10:00+00:00"),
        )

    @override_settings(TOKEN_CUT_OFF_DATETIME="10-1 10:00")
    @freeze_time("2025-10-01 10:00:01+00:00")
    def test_get_cut_off_moment_right_after(self):
        token_cut_off_datetime = get_token_cut_off()
        self.assertEqual(
            token_cut_off_datetime,
            datetime.fromisoformat("2026-10-01 10:00+00:00"),
        )

    @override_settings(TOKEN_CUT_OFF_DATETIME="13-1 10:00")
    def test_incorrect_cut_off_format(self):
        with self.assertRaises(ValueError):
            get_token_cut_off()
