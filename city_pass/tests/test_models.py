from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase
from freezegun import freeze_time

from city_pass.models import AccessToken, RefreshToken, Session


class TestTokenModels(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.session.save()
        self.date_format = "%Y-%m-%d %H:%M"

    def assert_is_valid_function(self, token_type):
        one_hour_in_seconds = 3600
        settings.TOKEN_TTLS = {
            "ACCESS_TOKEN": one_hour_in_seconds,
            "REFRESH_TOKEN": one_hour_in_seconds,
        }

        token_creation_time = datetime.strptime("2024-01-01 12:00", "%Y-%m-%d %H:%M")
        with freeze_time(token_creation_time):
            token = token_type(session=self.session)
            token.save()

        self.assertEqual(
            token.created_at.strftime(self.date_format),
            token_creation_time.strftime(self.date_format),
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
