from unittest import mock

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.middleware.log_4xx_status import log_4xx_status_middleware


class DatabaseRetryMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        patcher = mock.patch("core.middleware.log_4xx_status.logger")
        self.mock_logger = patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, body, status=200, release_version=None):
        response = HttpResponse(body, status=status)
        mw = log_4xx_status_middleware(lambda _req: response)
        headers = {}
        if release_version:
            headers["RELEASEVERSION"] = release_version
        request = self.factory.get("/test-endpoint/", headers=headers)
        return mw(request)

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
        self.assertIn(body, msg)
        self.assertIn(str(status), msg)

    def test_release_version_added_to_extra(self):
        body, status, version = "Bad Request", 400, "1.0.0"
        self._run(body, status, release_version=version)

        self.mock_logger.warning.assert_called_once()
        kwargs = self.mock_logger.warning.call_args.kwargs
        self.assertEqual(
            kwargs["extra"]["releaseVersion"],
            version,
        )
