from unittest import mock

from django.db import OperationalError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.middleware.db_retry_on_timeout import DatabaseRetryMiddleware

timeout_error = OperationalError(
    'connection to server at "aapp-p-asctypczqftak.postgres.database.azure.com" '
    "(10.225.95.68), port 5432 failed: Operation timed out\n"
    "Is the server running on that host and accepting TCP/IP connections?"
)


@mock.patch("core.middleware.db_retry_on_timeout.time.sleep", return_value=None)
class DatabaseRetryMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.logger_patcher = mock.patch("core.middleware.db_retry_on_timeout.logger")
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        self.logger_patcher.stop()

    def test_retry_on_timeout_always_fails(self, mock_sleep):
        """
        Test that the middleware retries the specified number of times
        when a connection timeout occurs and ultimately raises the exception.
        """

        def get_response(request):
            raise timeout_error

        middleware = DatabaseRetryMiddleware(get_response)

        # Create a dummy request
        request = self.factory.get("/test-endpoint/")

        # Invoke the middleware
        with self.assertRaises(OperationalError) as context:
            middleware(request)

        # Assert that the exception is the timeout error
        self.assertEqual(str(context.exception), str(timeout_error))

        # Assert that sleep was called the correct number of times
        expected_sleep_calls = [mock.call(1), mock.call(2), mock.call(4)]
        self.assertEqual(mock_sleep.call_args_list, expected_sleep_calls)

        # Assert that logger.warning was called for each retry
        self.assertEqual(self.mock_logger.warning.call_count, middleware.max_retries)
        for i in range(middleware.max_retries):
            self.mock_logger.warning.assert_any_call(
                f"OperationalError (timeout) encountered. Retrying request {i + 1}/{middleware.max_retries} after {1 * (2**i)} seconds."
            )

    def test_retry_on_timeout_then_succeed(self, mock_sleep):
        """
        Test that the middleware retries the specified number of times
        and succeeds if get_response eventually returns a response.
        """
        responses = [timeout_error, timeout_error, HttpResponse("Success")]

        def get_response(request):
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        middleware = DatabaseRetryMiddleware(get_response)

        # Create a dummy request
        request = self.factory.get("/test-endpoint/")

        # Invoke the middleware
        response = middleware(request)

        # Assert that the final response is the successful one
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")

        # Assert that sleep was called twice
        expected_sleep_calls = [mock.call(1), mock.call(2)]
        self.assertEqual(mock_sleep.call_args_list, expected_sleep_calls)

        # Assert that logger.warning was called twice
        self.assertEqual(self.mock_logger.warning.call_count, 2)
        for i in range(2):
            self.mock_logger.warning.assert_any_call(
                f"OperationalError (timeout) encountered. Retrying request {i + 1}/{middleware.max_retries} after {1 * (2**i)} seconds."
            )

    def test_no_retry_on_non_timeout_operational_error(self, mock_sleep):
        """
        Test that the middleware does not retry when an OperationalError
        with a different message is raised.
        """
        non_timeout_error = OperationalError("Some other operational error")

        def get_response(request):
            raise non_timeout_error

        middleware = DatabaseRetryMiddleware(get_response)

        # Create a dummy request
        request = self.factory.get("/test-endpoint/")

        # Invoke the middleware and expect the exception to be raised immediately
        with self.assertRaises(OperationalError) as context:
            middleware(request)

        # Assert that the exception is the non-timeout error
        self.assertEqual(str(context.exception), str(non_timeout_error))

        # Assert that sleep was not called
        mock_sleep.assert_not_called()

        # Assert that logger.warning was not called
        self.mock_logger.warning.assert_not_called()

    def test_no_retry_on_other_exception(self, mock_sleep):
        """
        Test that the middleware does not retry when a different exception
        is raised.
        """
        different_exception = ValueError("A different error occurred")

        def get_response(request):
            raise different_exception

        middleware = DatabaseRetryMiddleware(get_response)

        # Create a dummy request
        request = self.factory.get("/test-endpoint/")

        # Invoke the middleware and expect the exception to be raised immediately
        with self.assertRaises(ValueError) as context:
            middleware(request)

        # Assert that the exception is the one raised
        self.assertEqual(str(context.exception), str(different_exception))

        # Assert that sleep was not called
        mock_sleep.assert_not_called()

        # Assert that logger.warning was not called
        self.mock_logger.warning.assert_not_called()

    def test_retry_delays_exponential_backoff(self, mock_sleep):
        """
        Test that the middleware applies exponential backoff delays correctly.
        """
        responses = [timeout_error, HttpResponse("Success")]

        def get_response(request):
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        middleware = DatabaseRetryMiddleware(get_response)

        # Create a dummy request
        request = self.factory.get("/test-endpoint/")

        # Invoke the middleware
        response = middleware(request)

        # Assert that the final response is the successful one
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")

        # Assert that sleep was called once with initial_delay
        mock_sleep.assert_called_once_with(1)

        # Assert that logger.warning was called once
        self.mock_logger.warning.assert_called_once_with(
            f"OperationalError (timeout) encountered. Retrying request 1/{middleware.max_retries} after 1 seconds."
        )
