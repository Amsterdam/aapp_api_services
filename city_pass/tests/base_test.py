from django.conf import settings
from django.test import TestCase
from model_bakery import baker

from city_pass.models import AccessToken, RefreshToken, Session
from core.tests.test_authentication import ResponsesActivatedAPITestCase

DATE_FORMAT = "%Y-%m-%d %H:%M"
ONE_HOUR_IN_SECONDS = 3600


def set_up_city_pass_test_case(test_case) -> None:
    test_case.headers = {settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0]}

    test_case.session = baker.make(Session, encrypted_adminstration_no="foobar")
    baker.make(AccessToken, session=test_case.session)
    baker.make(RefreshToken, session=test_case.session)


class BaseCityPassTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        set_up_city_pass_test_case(self)


class ResponsesActivatedCityPassTestCase(ResponsesActivatedAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        set_up_city_pass_test_case(self)
