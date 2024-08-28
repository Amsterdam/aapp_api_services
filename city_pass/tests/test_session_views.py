from datetime import datetime, timedelta

from django.conf import settings
from django.test import override_settings
from freezegun import freeze_time
from model_bakery import baker

from city_pass.models import AccessToken, RefreshToken, Session
from city_pass.tests.base_test import (
    DATE_FORMAT,
    ONE_HOUR_IN_SECONDS,
    BaseCityPassTestCase,
)


class TestSessionInitView(BaseCityPassTestCase):
    api_url = "/city-pass/api/v1/session/init"

    def test_session_init_success(self):
        result = self.client.post(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)

        # Check if access token exists
        access_token_result = result.data.get("access_token")
        self.assertIsNotNone(access_token_result)
        self.assertNotEqual(access_token_result, "")
        access_token_obj = AccessToken.objects.filter(token=access_token_result).first()
        self.assertIsNotNone(access_token_obj)

        # Check if refresh token exists
        refresh_token_result = result.data.get("refresh_token")
        self.assertIsNotNone(refresh_token_result)
        self.assertNotEqual(refresh_token_result, "")
        refresh_token_obj = RefreshToken.objects.filter(
            token=refresh_token_result
        ).first()
        self.assertIsNotNone(refresh_token_obj)

        # Check if both tokens relate to the same session
        self.assertIsNotNone(access_token_obj.session)
        self.assertIsNotNone(refresh_token_obj.session)
        self.assertEqual(access_token_obj.session, refresh_token_obj.session)

    def test_session_init_invalid_api_key(self):
        result = self.client.get(self.api_url, headers=None, follow=True)
        self.assertEqual(result.status_code, 401)


class TestSessionPostCityPassCredentialView(BaseCityPassTestCase):
    api_url = "/city-pass/api/v1/session/credentials"

    def setUp(self) -> None:
        super().setUp()
        mijn_ams_api_keys = settings.MIJN_AMS_API_KEYS_OUTBOUND
        self.headers[settings.SESSION_CREDENTIALS_KEY_HEADER] = mijn_ams_api_keys.split(",")[0]

    def test_post_credentials_success(self):
        session = Session.objects.create()
        access_token = AccessToken(session=session)
        access_token.save()
        admin_no = "foobar"

        data = {
            "session_token": access_token.token,
            "encrypted_administration_no": admin_no,
        }
        result = self.client.post(
            self.api_url,
            headers=self.headers,
            data=data,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        session.refresh_from_db()
        self.assertEqual(session.encrypted_adminstration_no, admin_no)

    def test_post_credentials_session_token_invalid(self):
        data = {
            "session_token": "invalid_token",
            "encrypted_administration_no": "foobar",
        }

        result = self.client.post(
            self.api_url,
            headers=self.headers,
            data=data,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 401)
        self.assertContains(result, "TOKEN_INVALID", status_code=401)

    @override_settings(
        TOKEN_TTLS={
            "ACCESS_TOKEN": ONE_HOUR_IN_SECONDS,
        }
    )
    def test_post_credentials_session_token_expired(self):
        session = Session.objects.create()
        token_creation_time = datetime.strptime("2024-01-01 12:00", DATE_FORMAT)
        with freeze_time(token_creation_time):
            access_token = AccessToken(session=session)
            access_token.save()

        data = {
            "session_token": access_token.token,
            "encrypted_administration_no": "foobar",
        }

        token_usage_time = token_creation_time + timedelta(
            seconds=settings.TOKEN_TTLS["ACCESS_TOKEN"]
        )
        with freeze_time(token_usage_time):
            result = self.client.post(
                self.api_url,
                headers=self.headers,
                data=data,
                content_type="application/json",
                follow=True,
            )

        self.assertEqual(result.status_code, 401)
        self.assertContains(result, "expired", status_code=401)

    def test_post_credentials_missing_session_token(self):
        data = {
            "encrypted_administration_no": "foobar",
        }

        result = self.client.post(
            self.api_url,
            headers=self.headers,
            data=data,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 400)

    def test_post_credentials_missing_admin_no(self):
        session = Session.objects.create()
        access_token = AccessToken(session=session)
        access_token.save()

        data = {
            "session_token": access_token.token,
        }

        result = self.client.post(
            self.api_url,
            headers=self.headers,
            data=data,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 400)

    def test_default_api_key_not_allowed(self):
        headers = self.headers
        headers[settings.SESSION_CREDENTIALS_KEY_HEADER] = self.headers[settings.API_KEY_HEADER]
        result = self.client.post(
            self.api_url,
            headers=self.headers,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 401)


class TestSessionRefreshAccessView(BaseCityPassTestCase):
    api_url = "/city-pass/api/v1/session/refresh"

    @override_settings(
        TOKEN_TTLS={
            "REFRESH_TOKEN": ONE_HOUR_IN_SECONDS,
        }
    )
    def test_refresh_success(self):
        token_creation_time = datetime.strptime("2024-01-01 12:00", DATE_FORMAT)
        with freeze_time(token_creation_time):
            session = Session.objects.create()
            old_access_token_obj = AccessToken(session=session)
            old_access_token_obj.save()
            old_refresh_token_obj = RefreshToken(session=session)
            old_refresh_token_obj.save()

        token_refresh_time = token_creation_time + timedelta(minutes=30)
        with freeze_time(token_refresh_time):
            data = {
                "refresh_token": old_refresh_token_obj.token,
            }
            result = self.client.post(
                self.api_url,
                headers=self.headers,
                data=data,
                content_type="application/json",
                follow=True,
            )
            self.assertEqual(result.status_code, 200)

        # Assert if new access token exists
        access_token_result = result.data.get("access_token")
        self.assertIsNotNone(access_token_result)
        self.assertNotEqual(access_token_result, "")
        new_access_token_obj = AccessToken.objects.filter(
            token=access_token_result
        ).first()
        self.assertIsNotNone(new_access_token_obj)

        # Assert new access token is not the same as old
        self.assertNotEqual(old_access_token_obj.token, new_access_token_obj.token)
        self.assertTrue(
            new_access_token_obj.created_at > old_access_token_obj.created_at
        )

        # Assert that old access token is removed
        self.assertIsNone(
            AccessToken.objects.filter(pk=old_access_token_obj.pk).first()
        )

        # Assert if new refresh token exists
        refresh_token_result = result.data.get("refresh_token")
        self.assertIsNotNone(refresh_token_result)
        self.assertNotEqual(refresh_token_result, "")
        new_refresh_token_obj = RefreshToken.objects.filter(
            token=refresh_token_result
        ).first()
        self.assertIsNotNone(new_refresh_token_obj)

        # Assert new refresh token is not the same as old
        self.assertNotEqual(old_refresh_token_obj.token, new_refresh_token_obj.token)
        self.assertTrue(
            new_refresh_token_obj.created_at > old_refresh_token_obj.created_at
        )

        # Assert that old refresh token still exists
        self.assertIsNotNone(RefreshToken.objects.filter(pk=old_refresh_token_obj.pk))

        # Assert that old refresh token expires later then now
        old_refresh_token_obj.refresh_from_db()
        self.assertEqual(
            (
                token_refresh_time
                + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRATION_TIME)
            ).strftime(DATE_FORMAT),
            old_refresh_token_obj.expires_at.strftime(DATE_FORMAT),
        )

        # Assert that session has two refresh tokens
        session.refresh_from_db()
        self.assertEqual(len(session.refreshtoken_set.all()), 2)

    def test_invalid_refresh_token(self):
        data = {
            "refresh_token": "foobar",
        }
        result = self.client.post(
            self.api_url,
            headers=self.headers,
            data=data,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 401)

    def test_expired_refresh_token(self):
        token_creation_time = datetime.strptime("2024-01-01 12:00", DATE_FORMAT)
        with freeze_time(token_creation_time):
            session = Session.objects.create()
            access_token_obj = AccessToken(session=session)
            access_token_obj.save()
            refresh_token_obj = RefreshToken(session=session)
            refresh_token_obj.save()

        token_refresh_time = token_creation_time + timedelta(
            seconds=settings.REFRESH_TOKEN_TTL
        )
        with freeze_time(token_refresh_time):
            data = {
                "refresh_token": refresh_token_obj.token,
            }
            result = self.client.post(
                self.api_url,
                headers=self.headers,
                data=data,
                content_type="application/json",
                follow=True,
            )
            self.assertEqual(result.status_code, 401)


class TestSessionLogoutView(BaseCityPassTestCase):
    api_url = "/city-pass/api/v1/session/logout"

    def test_logout_success(self):
        headers = {**self.headers, "Access-Token": self.session.accesstoken.token}
        result = self.client.post(
            self.api_url,
            headers=headers,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        self.assertIsNone(AccessToken.objects.first())
        self.assertIsNone(RefreshToken.objects.first())

    def test_logout_invalid_session_token(self):
        headers = {**self.headers, "Access-Token": "invalid"}
        result = self.client.post(
            self.api_url,
            headers=headers,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 401)

    def test_logout_without_session_token(self):
        result = self.client.post(
            self.api_url,
            headers=self.headers,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 401)

    def test_other_sessions_unaffected(self):
        other_session_1 = baker.make(Session, encrypted_adminstration_no="barfoo")
        baker.make(AccessToken, session=other_session_1)
        baker.make(RefreshToken, session=other_session_1)

        other_session_2 = baker.make(Session, encrypted_adminstration_no="barfoo")
        baker.make(AccessToken, session=other_session_2)
        baker.make(RefreshToken, session=other_session_2)

        headers = {**self.headers, "Access-Token": self.session.accesstoken.token}
        result = self.client.post(
            self.api_url,
            headers=headers,
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        self.assertEqual(AccessToken.objects.count(), 2)
        self.assertEqual(RefreshToken.objects.count(), 2)
        self.assertEqual(
            len(Session.objects.filter(encrypted_adminstration_no="foobar")), 0
        )
        self.assertEqual(
            len(Session.objects.filter(encrypted_adminstration_no="barfoo")), 2
        )
