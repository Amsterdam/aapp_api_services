from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from freezegun import freeze_time

from city_pass.models import AccessToken, RefreshToken, Session
from city_pass.tests.base_test import DATE_FORMAT, ONE_HOUR_IN_SECONDS


class TestTokenModels(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.session.save()

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
            self.assertTrue(token.is_valid())

        # Precisly 1 hour after creation token is invalid
        with freeze_time(token_creation_time + timedelta(hours=1)):
            self.assertFalse(token.is_valid())

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
            self.assertTrue(refresh_token.is_valid())
            refresh_token.expire()

        token_expired_time = token_creation_time + timedelta(hours=1)
        with freeze_time(token_expired_time):
            self.assertFalse(refresh_token.is_valid())
