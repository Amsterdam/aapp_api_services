import json
from unittest.mock import patch

from requests import Response

from contact.services.service_abstract import ServiceAbstract
from contact.tests.mock_data import toilets
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class MockService(ServiceAbstract):
    data_url = "mock-url"

    def __init__(self) -> None:
        super().__init__()


class ServiceAbstractTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = MockService()

    @patch("contact.services.service_abstract.requests.get")
    def test_make_request_succeeds_after_retry(self, mock_get):
        # Simulate a 500 error on the first request
        mock_response_1 = Response()
        mock_response_1.status_code = 500
        mock_response_1._content = json.dumps(
            {"status": "ERROR", "message": "Internal Server Error"}
        ).encode("utf-8")

        # Simulate a successful response on the second request
        mock_response_2 = Response()
        mock_response_2.status_code = 200
        mock_response_2._content = json.dumps(
            {"content": toilets.MOCK_DATA, "status": "SUCCESS"}
        ).encode("utf-8")

        mock_get.side_effect = [mock_response_1, mock_response_2]

        resp = self.service._make_request()
        self.assertEqual(resp.status_code, 200)

    def test_assert_data_url_defined(self):
        with self.assertRaises(NotImplementedError):

            class InvalidService(ServiceAbstract):
                pass

            InvalidService()
