from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.middleware.set_headers import DefaultHeadersMiddleware


class TestDefaultHeadersMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = DefaultHeadersMiddleware(self.get_response)

    def get_response(self, request):
        return HttpResponse()

    def test_adds_charset_to_existing_content_type(self):
        request = self.factory.get("/")
        response = HttpResponse()
        response["Content-Type"] = "application/json"

        self.middleware.get_response = lambda r: response
        processed_response = self.middleware(request)

        self.assertEqual(
            processed_response["Content-Type"],
            "application/json; charset=UTF-8",
        )

    def test_preserves_existing_charset(self):
        request = self.factory.get("/")
        response = HttpResponse()
        response["Content-Type"] = "application/json; charset=ISO-8859-1"

        self.middleware.get_response = lambda r: response
        processed_response = self.middleware(request)

        self.assertEqual(
            processed_response["Content-Type"],
            "application/json; charset=ISO-8859-1",
        )

    def test_sets_default_content_type_when_missing(self):
        request = self.factory.get("/")
        response = HttpResponse()
        response["Content-Type"] = ""  # or don't set it at all

        self.middleware.get_response = lambda r: response
        processed_response = self.middleware(request)

        self.assertEqual(
            processed_response["Content-Type"],
            "application/json; charset=UTF-8",
        )
