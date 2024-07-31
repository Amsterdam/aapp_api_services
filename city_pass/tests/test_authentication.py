from datetime import datetime, timedelta

from django.conf import settings
from django.test import RequestFactory, TestCase
from freezegun import freeze_time
from rest_framework.exceptions import AuthenticationFailed

from city_pass.authentication import AccessTokenAuthentication
from city_pass.models import AccessToken, Session
from city_pass.tests.test_session_views import DATE_FORMAT


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

        token_authenticator = AccessTokenAuthentication()
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

        with self.assertRaises(AuthenticationFailed):
            token_authenticator = AccessTokenAuthentication()
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
            "/some-endpoint/", headers={self.header_name: "invalid_token"}
        )

        token_authenticate_time = token_creation_time + timedelta(
            seconds=settings.ACCESS_TOKEN_TTL
        )
        with freeze_time(token_authenticate_time):
            with self.assertRaises(AuthenticationFailed):
                token_authenticator = AccessTokenAuthentication()
                token_authenticator.authenticate(request)

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

        with self.assertRaises(AuthenticationFailed):
            token_authenticator = AccessTokenAuthentication()
            token_authenticator.authenticate(request)
