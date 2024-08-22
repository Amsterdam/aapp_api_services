from django.test import TestCase, override_settings
from model_bakery import baker

from city_pass.models import Session, AccessToken, RefreshToken

DATE_FORMAT = "%Y-%m-%d %H:%M"
ONE_HOUR_IN_SECONDS = 3600
MOCK_API_KEY = "amsterdam"


class BaseCityPassTestCase(TestCase):
    def setUp(self) -> None:
        self.override = override_settings(API_KEYS=[MOCK_API_KEY])
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.headers = {"X-API-KEY": MOCK_API_KEY}

        self.session = baker.make(Session, encrypted_adminstration_no="foobar")
        baker.make(AccessToken, session=self.session)
        baker.make(RefreshToken, session=self.session)
