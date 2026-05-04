from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import translation

from core.middleware.force_admin_language import force_admin_language_middleware


class TestForceAdminLanguageMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.original_language = translation.get_language()
        self.addCleanup(translation.activate, self.original_language)

    def _response_with_language_headers(self, request):
        response = HttpResponse()
        response["X-Active-Language"] = translation.get_language() or ""
        response["X-Request-Language"] = getattr(request, "LANGUAGE_CODE", "") or ""
        return response

    def test_sync_admin_path_forces_nl(self):
        translation.activate("en")
        prior_language = translation.get_language()

        request = self.factory.get("/admin/somewhere/")

        def get_response(req):
            return self._response_with_language_headers(req)

        middleware = force_admin_language_middleware(get_response)
        response = middleware(request)

        self.assertEqual(response["X-Request-Language"], "nl-NL")
        self.assertTrue(response["X-Active-Language"].lower().startswith("nl"))
        # Ensure the global language is not changed by the middleware
        self.assertEqual(translation.get_language(), prior_language)

    def test_sync_non_admin_path_does_not_override(self):
        translation.activate("en")
        prior_language = translation.get_language()

        request = self.factory.get("/api/v1/health/")

        def get_response(req):
            return self._response_with_language_headers(req)

        middleware = force_admin_language_middleware(get_response)
        response = middleware(request)

        self.assertEqual(response["X-Request-Language"], "")
        self.assertEqual(response["X-Active-Language"], prior_language or "")
        self.assertEqual(translation.get_language(), prior_language)

    def test_async_admin_path_forces_nl(self):
        translation.activate("en")
        prior_language = translation.get_language()

        request = self.factory.get("/admin/async/")

        async def get_response(req):
            return self._response_with_language_headers(req)

        middleware = force_admin_language_middleware(get_response)
        response = async_to_sync(middleware)(request)

        self.assertEqual(response["X-Request-Language"], "nl-NL")
        self.assertTrue(response["X-Active-Language"].lower().startswith("nl"))
        self.assertEqual(translation.get_language(), prior_language)

    def test_async_non_admin_path_does_not_override(self):
        translation.activate("en")
        prior_language = translation.get_language()

        request = self.factory.get("/api/v1/health/")

        async def get_response(req):
            return self._response_with_language_headers(req)

        middleware = force_admin_language_middleware(get_response)
        response = async_to_sync(middleware)(request)

        self.assertEqual(response["X-Request-Language"], "")
        self.assertEqual(response["X-Active-Language"], prior_language or "")
        self.assertEqual(translation.get_language(), prior_language)
