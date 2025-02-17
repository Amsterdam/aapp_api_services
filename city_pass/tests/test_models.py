from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from freezegun import freeze_time

from city_pass.exceptions import TokenExpiredException
from city_pass.models import AccessToken, RefreshToken, Session
from city_pass.tests.base_test import DATE_FORMAT, ONE_HOUR_IN_SECONDS


class TestTokenModels(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.session.save()

    def assert_token_valid(self, token):
        """
        Assert that token is valid.
        Scenarios:
        - Test passes, if exception is not raised
        - Test failes, if exception is raised
        """
        try:
            token.is_valid()
        except TokenExpiredException:
            self.fail("Token is invalid")

    def assert_token_invalid(self, token):
        """
        Assert that token is invalid.
        Scenarios:
        - Test passes, if exception is raised
        - Test fails, if exception is not raised
        """
        try:
            token.is_valid()
        except TokenExpiredException:
            return

        self.fail("Token is valid")

    @override_settings(
        TOKEN_TTLS={
            "ACCESS_TOKEN": ONE_HOUR_IN_SECONDS,
            "REFRESH_TOKEN": ONE_HOUR_IN_SECONDS,
        }
    )
    def assert_is_valid_function(self, token_type):
        token_creation_time = datetime.strptime("2024-01-01 12:00", "%Y-%m-%d %H:%M")
        with freeze_time(token_creation_time):
            token = token_type(session=self.session)
            token.save()

        self.assertEqual(
            token.created_at.strftime(DATE_FORMAT),
            token_creation_time.strftime(DATE_FORMAT),
        )

        # One second before expiration token is still valid
        with freeze_time(token_creation_time + timedelta(minutes=59)):
            self.assert_token_valid(token)

        # Precisly 1 hour after creation token is invalid
        with freeze_time(token_creation_time + timedelta(hours=1)):
            self.assert_token_invalid(token)

    def test_access_token_is_valid_function(self):
        self.assert_is_valid_function(AccessToken)

    def test_refresh_token_is_valid_function(self):
        self.assert_is_valid_function(RefreshToken)

    @override_settings(REFRESH_TOKEN_EXPIRATION_TIME=ONE_HOUR_IN_SECONDS)
    def test_refresh_token_is_expired(self):
        token_creation_time = datetime.strptime("2024-01-01 12:00", "%Y-%m-%d %H:%M")
        with freeze_time(token_creation_time):
            refresh_token = RefreshToken(session=self.session)
            refresh_token.save()
            self.assert_token_valid(refresh_token)
            refresh_token.expire()

        token_expired_time = token_creation_time + timedelta(hours=1)
        with freeze_time(token_expired_time):
            self.assert_token_invalid(refresh_token)

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="10-1 10:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": 4 * 365 * 24 * 60 * 60,  # 4 years in seconds
            "REFRESH_TOKEN": 4 * 365 * 24 * 60 * 60,  # 4 years in seconds,
        },
    )
    def test_token_created_before_cut_off(self):
        creation_time_before_cut_off = datetime.strptime(
            "2022-01-01 12:00", "%Y-%m-%d %H:%M"
        )
        with freeze_time(creation_time_before_cut_off):
            access_token = AccessToken(session=self.session)
            access_token.save()
            self.assert_token_valid(access_token)

            refresh_token = RefreshToken(session=self.session)
            refresh_token.save()
            self.assert_token_valid(refresh_token)

        before_cut_off_datetime = datetime.strptime(
            "2024-10-01 09:59", "%Y-%m-%d %H:%M"
        )
        with freeze_time(before_cut_off_datetime):
            self.assert_token_valid(access_token)
            self.assert_token_valid(refresh_token)

            # Check that tokens are still in the database
            self.assertEqual(AccessToken.objects.count(), 1)
            self.assertEqual(RefreshToken.objects.count(), 1)

        after_cut_off_datetime = datetime.strptime("2024-10-01 10:01", "%Y-%m-%d %H:%M")
        with freeze_time(after_cut_off_datetime):
            self.assert_token_invalid(access_token)
            self.assert_token_invalid(refresh_token)

            # Check that tokens are deleted from the database
            self.assertEqual(AccessToken.objects.count(), 0)
            self.assertEqual(RefreshToken.objects.count(), 0)

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="10-1 10:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": 4 * 365 * 24 * 60 * 60,  # 4 years in seconds
            "REFRESH_TOKEN": 4 * 365 * 24 * 60 * 60,  # 4 years in seconds,
        },
    )
    def test_token_created_after_cut_off(self):
        creation_time_after_cut_off = datetime.strptime(
            "2024-10-01 10:01", "%Y-%m-%d %H:%M"
        )
        with freeze_time(creation_time_after_cut_off):
            access_token = AccessToken(session=self.session)
            access_token.save()
            self.assert_token_valid(access_token)

            refresh_token = RefreshToken(session=self.session)
            refresh_token.save()
            self.assert_token_valid(refresh_token)

        after_cut_off_datetime = datetime.strptime("2024-10-01 10:01", "%Y-%m-%d %H:%M")
        with freeze_time(after_cut_off_datetime):
            self.assert_token_valid(access_token)
            self.assert_token_valid(refresh_token)

            # Check that tokens are still in the database
            self.assertEqual(AccessToken.objects.count(), 1)
            self.assertEqual(RefreshToken.objects.count(), 1)
