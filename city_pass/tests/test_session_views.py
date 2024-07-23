from django.test import TestCase
from django.conf import settings

from city_pass.models import AccessToken, RefreshToken


class TestSessionInitView(TestCase):
    def setUp(self):
        self.api_url = "/city-pass/api/v1/session/init"
        
        settings.API_KEYS = ["amsterdam"]
        self.headers = {
            "X-API-KEY": "amsterdam"
        }

    def test_session_init_success(self):
        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)
        
        # Check if access token exists
        access_token_result = result.data.get("access_token")
        self.assertIsNotNone(access_token_result)
        self.assertNotEqual(access_token_result, '')
        access_token_obj = AccessToken.objects.filter(token=access_token_result).first()
        self.assertIsNotNone(access_token_obj)

        # Check if refresh token exists
        refresh_token_result = result.data.get("refresh_token")
        self.assertIsNotNone(refresh_token_result)
        self.assertNotEqual(refresh_token_result, '')
        refresh_token_obj = RefreshToken.objects.filter(token=refresh_token_result).first()
        self.assertIsNotNone(refresh_token_obj)

        # Check if both tokens relate to the same session
        self.assertIsNotNone(access_token_obj.session)
        self.assertIsNotNone(refresh_token_obj.session)
        self.assertEqual(access_token_obj.session, refresh_token_obj.session)

    def test_session_init_invalid_api_key(self):
        result = self.client.get(self.api_url, headers=None, follow=True)
        self.assertEqual(result.status_code, 403)
    
    