import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_READ_TIMEOUT = 10
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF_FACTOR = 0.5


class TimeoutSession(requests.Session):
    """requests.Session with a default timeout applied to every request."""

    def request(self, method, url, **kwargs):
        if "timeout" not in kwargs or kwargs["timeout"] is None:
            kwargs["timeout"] = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
        return super().request(method, url, **kwargs)


def build_safe_session():
    """Returns a Session with safe defaults."""
    session = TimeoutSession()

    retry = Retry(
        total=DEFAULT_RETRIES,
        backoff_factor=DEFAULT_BACKOFF_FACTOR,  # Exponential backoff
        status_forcelist=(502, 503, 504),
        allowed_methods=(
            "GET",
            "HEAD",
            "OPTIONS",
            "PUT",
            "DELETE",
            "POST",
            "PATCH",
        ),  # Assuming that our requests are always idempotent
        raise_on_status=False,  # Let the client handle the status code
    )

    adapter = HTTPAdapter(max_retries=retry)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class InternalServiceHttpClient:
    """A reusable HTTP client with safe defaults."""

    def __init__(self):
        self.session = build_safe_session()
        if getattr(settings, "DISABLE_SAFE_HTTP_INTERNAL", False):
            self.session = requests.Session()

        self._base_headers = {
            settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0],
        }

    def request(self, method, url, **kwargs):
        """Make a request with safe defaults."""
        # Set default headers if not provided
        final_headers = self._base_headers.copy()
        if "headers" in kwargs and kwargs["headers"] is not None:
            final_headers.update(kwargs["headers"])
        kwargs["headers"] = final_headers

        return self.session.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)
