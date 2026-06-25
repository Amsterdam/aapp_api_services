from datetime import datetime

from django.test import TestCase, override_settings
from freezegun import freeze_time

from city_pass.utils import get_token_cut_off


class TestUtils(TestCase):
    @override_settings(TOKEN_CUT_OFF_DATETIME="08-01 00:00")
    @freeze_time("2026-07-31 21:59:59+00:00")
    def test_get_cut_off_moment_just_before_amsterdam_boundary(self):
        token_cut_off_datetime = get_token_cut_off()
        self.assertEqual(
            token_cut_off_datetime,
            datetime.fromisoformat("2026-08-01 00:00:00+02:00"),
        )

    @override_settings(TOKEN_CUT_OFF_DATETIME="08-01 00:00")
    @freeze_time("2026-07-31 22:00:00+00:00")
    def test_get_cut_off_moment_equal_to_amsterdam_boundary(self):
        token_cut_off_datetime = get_token_cut_off()
        self.assertEqual(
            token_cut_off_datetime,
            datetime.fromisoformat("2026-08-01 00:00:00+02:00"),
        )

    @override_settings(TOKEN_CUT_OFF_DATETIME="08-01 00:00")
    @freeze_time("2026-07-31 22:00:01+00:00")
    def test_get_cut_off_moment_right_after_amsterdam_boundary(self):
        token_cut_off_datetime = get_token_cut_off()
        self.assertEqual(
            token_cut_off_datetime,
            datetime.fromisoformat("2027-08-01 00:00:00+02:00"),
        )

    @override_settings(TOKEN_CUT_OFF_DATETIME="13-1 10:00")
    def test_incorrect_cut_off_format(self):
        with self.assertRaises(ValueError):
            get_token_cut_off()
