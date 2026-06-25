from datetime import datetime, timedelta

from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from freezegun import freeze_time

from city_pass.authentication import AccessTokenWithAdminNrAuthentication
from city_pass.exceptions import (
    TokenExpiredException,
    TokenInvalidException,
    TokenNotReadyException,
)
from city_pass.models import AccessToken, Session
from city_pass.tests.views.test_session_views import DATE_FORMAT


class TestAuthenicateAccessToken(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.header_name = settings.ACCESS_TOKEN_HEADER

    @freeze_time("2024-01-01 12:00")
    def test_populated_session_with_valid_access_token(self):
        """
        Session has (encrypted) administration number,
        and access token is still valid.
        """
        session = Session.objects.create()
        session.encrypted_adminstration_no = "foobar"
        session.save()

        access_token = AccessToken(session=session)
        access_token.save()

        request = self.factory.get(
            "/some-endpoint/", headers={self.header_name: access_token.token}
        )

        token_authenticator = AccessTokenWithAdminNrAuthentication()
        result_session, result_token = token_authenticator.authenticate(request)

        self.assertEqual(result_session, access_token.session)
        self.assertEqual(result_token, access_token)

    def test_invalid_access_token(self):
        """
        Unknown access token is passed
        """
        request = self.factory.get(
            "/some-endpoint/", headers={self.header_name: "invalid_token"}
        )

        with self.assertRaises(TokenInvalidException):
            token_authenticator = AccessTokenWithAdminNrAuthentication()
            token_authenticator.authenticate(request)

    def test_expired_access_token(self):
        """
        Access token is expired
        """
        token_creation_time = datetime.strptime("2024-01-01 12:00", DATE_FORMAT)
        with freeze_time(token_creation_time):
            session = Session.objects.create()
            access_token = AccessToken(session=session)
            access_token.save()

        request = self.factory.get(
            "/some-endpoint/", headers={self.header_name: access_token.token}
        )

        token_authenticate_time = token_creation_time + timedelta(
            seconds=settings.ACCESS_TOKEN_TTL
        )
        with freeze_time(token_authenticate_time):
            with self.assertRaises(TokenExpiredException):
                token_authenticator = AccessTokenWithAdminNrAuthentication()
                token_authenticator.authenticate(request)

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="08-01 00:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": 365 * 24 * 60 * 60,
            "REFRESH_TOKEN": 365 * 24 * 60 * 60,
        },
    )
    def test_pre_cut_off_access_token_is_accepted_just_before_amsterdam_boundary(self):
        with freeze_time("2026-07-31 21:59:58+00:00"):
            session = Session.objects.create(encrypted_adminstration_no="foobar")
            access_token = AccessToken.objects.create(session=session)

        request = self.factory.get(
            "/some-endpoint/", headers={self.header_name: access_token.token}
        )

        with freeze_time("2026-07-31 21:59:59+00:00"):
            token_authenticator = AccessTokenWithAdminNrAuthentication()
            result_session, result_token = token_authenticator.authenticate(request)

        self.assertEqual(result_session, access_token.session)
        self.assertEqual(result_token, access_token)

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="08-01 00:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": 365 * 24 * 60 * 60,
            "REFRESH_TOKEN": 365 * 24 * 60 * 60,
        },
    )
    def test_pre_cut_off_access_token_is_rejected_at_amsterdam_boundary(self):
        with freeze_time("2026-07-31 21:59:59+00:00"):
            session = Session.objects.create(encrypted_adminstration_no="foobar")
            access_token = AccessToken.objects.create(session=session)

        request = self.factory.get(
            "/some-endpoint/", headers={self.header_name: access_token.token}
        )

        with freeze_time("2026-07-31 22:00:00+00:00"):
            with self.assertRaises(TokenExpiredException):
                token_authenticator = AccessTokenWithAdminNrAuthentication()
                token_authenticator.authenticate(request)

        self.assertFalse(AccessToken.objects.filter(pk=access_token.pk).exists())

    @override_settings(
        TOKEN_CUT_OFF_DATETIME="08-01 00:00",
        TOKEN_TTLS={
            "ACCESS_TOKEN": 365 * 24 * 60 * 60,
            "REFRESH_TOKEN": 365 * 24 * 60 * 60,
        },
    )
    def test_post_cut_off_access_token_is_accepted_after_fresh_login(self):
        with freeze_time("2026-07-31 22:00:00+00:00"):
            session = Session.objects.create(encrypted_adminstration_no="foobar")
            access_token = AccessToken.objects.create(session=session)

        request = self.factory.get(
            "/some-endpoint/", headers={self.header_name: access_token.token}
        )

        with freeze_time("2026-07-31 22:00:01+00:00"):
            token_authenticator = AccessTokenWithAdminNrAuthentication()
            result_session, result_token = token_authenticator.authenticate(request)

        self.assertEqual(result_session, access_token.session)
        self.assertEqual(result_token, access_token)

    @freeze_time("2024-01-01 12:00")
    def test_unpopulated_session(self):
        """
        Session doesn't have an encrypted administration number
        """
        session = Session.objects.create()
        access_token = AccessToken(session=session)
        access_token.save()

        request = self.factory.get(
            "/some-endpoint/", headers={self.header_name: access_token.token}
        )

        with self.assertRaises(TokenNotReadyException):
            token_authenticator = AccessTokenWithAdminNrAuthentication()
            token_authenticator.authenticate(request)
