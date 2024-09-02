from django.conf import settings
from django.test import TestCase
from model_bakery import baker

from city_pass.models import AccessToken, RefreshToken, Session

DATE_FORMAT = "%Y-%m-%d %H:%M"
ONE_HOUR_IN_SECONDS = 3600


class BaseCityPassTestCase(TestCase):
    def setUp(self) -> None:
        self.headers = {settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]}

        self.session = baker.make(Session, encrypted_adminstration_no="foobar")
        baker.make(AccessToken, session=self.session)
        baker.make(RefreshToken, session=self.session)
