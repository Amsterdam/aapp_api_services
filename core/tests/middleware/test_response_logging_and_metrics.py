from unittest import mock

from asgiref.sync import async_to_sync
from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory, TestCase

from core.middleware.response_logging_and_metrics import (
    handle_response_metrics_and_4xx_logging_middleware,
)


class ResponseLoggingAndMetricsMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        patcher = mock.patch("core.middleware.response_logging_and_metrics.logger")
        self.mock_logger = patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, body=None, status=200, release_version=None, response=None):
        response = response or HttpResponse(body, status=status)
        mw = handle_response_metrics_and_4xx_logging_middleware(lambda _req: response)
        headers = {}
        if release_version:
            headers["RELEASEVERSION"] = release_version
        request = self.factory.get("/test-endpoint/", headers=headers)
        return mw(request)

    def test_success_response_updates_metrics_counter(self):
        with mock.patch(
            "core.middleware.response_logging_and_metrics.successful_requests_counter"
        ) as mock_counter:
            self._run("OK", status=200)

        mock_counter.add.assert_called_once_with(
            1,
            {
                "method": "GET",
                "path": "/test-endpoint/",
            },
        )

    def test_metrics_counter_not_updated_for_4xx(self):
        with mock.patch(
            "core.middleware.response_logging_and_metrics.successful_requests_counter"
        ) as mock_counter:
            self._run("Bad Request", status=400)

        mock_counter.add.assert_not_called()

    def test_metrics_errors_do_not_break_request_flow(self):
        with mock.patch(
            "core.middleware.response_logging_and_metrics.successful_requests_counter"
        ) as mock_counter:
            mock_counter.add.side_effect = RuntimeError("metrics backend unavailable")
            response = self._run("OK", status=200)

        self.assertEqual(200, response.status_code)

    def test_no_logging_success(self):
        self._run("OK")
        self.mock_logger.warning.assert_not_called()

    def test_no_logging_500(self):
        self._run("ERROR", 500)
        self.mock_logger.warning.assert_not_called()

    def test_400_response_logged(self):
        body, status = "Bad Request", 400
        self._run(body, status)

        self.mock_logger.warning.assert_called_once()
        msg = self.mock_logger.warning.call_args.args[0]
        self.assertEqual("GET /test-endpoint/", msg)
        extra = self.mock_logger.warning.call_args.kwargs.get("extra", {})
        self.assertEqual(body, extra["body"])
        self.assertEqual(status, extra["status"])

    def test_release_version_added_to_extra(self):
        body, status, version = "Bad Request", 400, "1.0.0"
        self._run(body, status, release_version=version)

        self.mock_logger.warning.assert_called_once()
        kwargs = self.mock_logger.warning.call_args.kwargs
        self.assertEqual(
            kwargs["extra"]["releaseVersion"],
            version,
        )

    def test_4xx_logging_includes_full_path(self):
        self._run("Not Found", status=404)

        kwargs = self.mock_logger.warning.call_args.kwargs
        self.assertEqual("/test-endpoint/", kwargs["extra"]["full_path"])

    def test_4xx_streaming_response_does_not_read_body(self):
        streaming_response = StreamingHttpResponse(
            streaming_content=[b"streamed"],
            status=404,
        )
        self._run(response=streaming_response)

        kwargs = self.mock_logger.warning.call_args.kwargs
        self.assertEqual("", kwargs["extra"]["body"])

    def test_4xx_logging_errors_are_captured(self):
        self.mock_logger.warning.side_effect = RuntimeError("logging failed")

        self._run("Bad Request", status=400)

        self.mock_logger.error.assert_called_once()
        msg = self.mock_logger.error.call_args.args[0]
        self.assertIn("Error logging 4xx response:", msg)
        self.assertEqual(
            {
                "request_method": "GET",
                "request_path": "/test-endpoint/",
            },
            self.mock_logger.error.call_args.kwargs["extra"],
        )

    def test_async_middleware_path(self):
        response = HttpResponse("OK", status=200)

        async def get_response(_request):
            return response

        middleware = handle_response_metrics_and_4xx_logging_middleware(get_response)
        request = self.factory.get("/test-endpoint/")
        result = async_to_sync(middleware)(request)

        self.assertEqual(response, result)
