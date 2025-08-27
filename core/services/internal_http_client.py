import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_READ_TIMEOUT = 10
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF_FACTOR = 0.5
RETRY_ON_STATUS_CODES = (502, 503, 504)


class InternalServiceSession(requests.Session):
    """A reusable HTTP client with safe defaults."""

    def __init__(self):
        super().__init__()

        adapter = HTTPAdapter(max_retries=self._retry_config)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

        self.headers.update(
            {
                settings.API_KEY_HEADER: settings.API_KEYS.split(",")[0],
            }
        )

    @property
    def _retry_config(self):
        return Retry(
            total=DEFAULT_RETRIES,
            backoff_factor=DEFAULT_BACKOFF_FACTOR,
            status_forcelist=RETRY_ON_STATUS_CODES,
            allowed_methods=(
                "GET",
                "HEAD",
                "OPTIONS",
                "PUT",
                "DELETE",
                "POST",
                "PATCH",
            ),
            raise_on_status=False,
        )

    def request(self, method, url, **kwargs):
        """Make a request with safe defaults."""
        # Handle DISABLE_SAFE_HTTP_INTERNAL setting
        if getattr(settings, "DISABLE_SAFE_HTTP_INTERNAL", False):  # pragma: no cover
            # Create a temporary session without retries for this request
            temp_session = requests.Session()
            temp_session.headers.update(self.headers)
            return temp_session.request(method, url, **kwargs)

        # Apply default timeout if not provided
        if "timeout" not in kwargs or kwargs["timeout"] is None:
            kwargs["timeout"] = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)

        return super().request(method, url, **kwargs)
