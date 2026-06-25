from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase, override_settings
from freezegun import freeze_time

from city_pass.models import AccessToken, RefreshToken, Session
from city_pass.serializers.session_serializers import SessionTokensOutSerializer
from city_pass.tests.base_test import ONE_HOUR_IN_SECONDS
from city_pass.utils import get_token_cut_off


class TestSessionTokensOutSerializer(TestCase):
    def setUp(self):
        self.serializer_class = SessionTokensOutSerializer
        self.session = Session.objects.create()

    def assert_expiration_dt_related_to_ttl(
        self, frozen_time, token_type, token_exp_datetime
    ):
        token_exp_datetime_expected = frozen_time + timedelta(
            seconds=settings.TOKEN_TTLS[token_type]
        )
        self.assertTrue(token_exp_datetime == token_exp_datetime_expected)

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="08-01 10:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": ONE_HOUR_IN_SECONDS,  # 1 hour
            "REFRESH_TOKEN": ONE_HOUR_IN_SECONDS * 2,  # 2 hours
        },
    )
    def test_token_exp_way_before_token_cut_off(self):
        # Way before cut off datetime
        freeze_time_at = datetime.fromisoformat("2025-01-01 12:00:00+01:00")
        with freeze_time(freeze_time_at):
            access_token = AccessToken.objects.create(session=self.session)
            refresh_token = RefreshToken.objects.create(session=self.session)
            serializer_output = self.serializer_class((access_token, refresh_token))

        # Expiration dates should be related to token ttl
        self.assert_expiration_dt_related_to_ttl(
            freeze_time_at,
            "ACCESS_TOKEN",
            serializer_output.data["access_token_expiration"],
        )
        self.assert_expiration_dt_related_to_ttl(
            freeze_time_at,
            "REFRESH_TOKEN",
            serializer_output.data["refresh_token_expiration"],
        )

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="08-01 10:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": ONE_HOUR_IN_SECONDS,  # 1 hour
            "REFRESH_TOKEN": ONE_HOUR_IN_SECONDS * 2,  # 2 hours
        },
    )
    def test_token_exp_right_after_token_cut_off(self):
        # Right after cut off datetime
        freeze_time_at = datetime.fromisoformat("2025-08-01 10:00:01+02:00")
        with freeze_time(freeze_time_at):
            access_token = AccessToken.objects.create(session=self.session)
            refresh_token = RefreshToken.objects.create(session=self.session)
            serializer_output = self.serializer_class((access_token, refresh_token))

        # Expiration dates should again be related to token ttl
        self.assert_expiration_dt_related_to_ttl(
            freeze_time_at,
            "ACCESS_TOKEN",
            serializer_output.data["access_token_expiration"],
        )
        self.assert_expiration_dt_related_to_ttl(
            freeze_time_at,
            "REFRESH_TOKEN",
            serializer_output.data["refresh_token_expiration"],
        )

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="08-01 10:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": ONE_HOUR_IN_SECONDS,  # 1 hour
            "REFRESH_TOKEN": ONE_HOUR_IN_SECONDS * 2,  # 2 hours
        },
    )
    def test_token_exp_is_cut_off_at_and_before_boundary(self):
        for freeze_time_at in (
            datetime.fromisoformat("2025-08-01 09:30:00+02:00"),
            datetime.fromisoformat("2025-08-01 10:00:00+02:00"),
        ):
            with freeze_time(freeze_time_at):
                session = Session.objects.create()
                access_token = AccessToken.objects.create(session=session)
                refresh_token = RefreshToken.objects.create(session=session)
                serializer_output = self.serializer_class((access_token, refresh_token))
                token_cut_off_datetime = get_token_cut_off()
                # Evaluate serializer fields inside frozen time to avoid lazy-evaluation drift.
                access_token_expiration = serializer_output.data[
                    "access_token_expiration"
                ]
                refresh_token_expiration = serializer_output.data[
                    "refresh_token_expiration"
                ]

            self.assertEqual(access_token_expiration, token_cut_off_datetime)
            self.assertEqual(refresh_token_expiration, token_cut_off_datetime)
