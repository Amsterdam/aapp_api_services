from django.conf import settings
from django.test import TestCase

from city_pass.models import AccessToken, RefreshToken, Session


class TestSessionInitView(TestCase):
    def setUp(self):
        self.api_url = "/city-pass/api/v1/session/init"

        settings.API_KEYS = ["amsterdam"]
        self.headers = {"X-API-KEY": "amsterdam"}

    def test_session_init_success(self):
        result = self.client.get(self.api_url, headers=self.headers, follow=True)
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
        self.assertEqual(result.status_code, 403)


class TestSessionPostCityPassCredentialView(TestCase):
    def setUp(self):
        self.api_url = "/city-pass/api/v1/session/credentials"

        settings.API_KEYS = ["amsterdam"]
        self.headers = {"X-API-KEY": "amsterdam"}

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
