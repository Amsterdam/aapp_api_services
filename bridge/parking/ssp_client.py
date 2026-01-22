import httpx
from django.conf import settings

TIMEOUT = httpx.Timeout(
    connect=2.0,
    read=settings.SSP_API_TIMEOUT_SECONDS,
    write=settings.SSP_API_TIMEOUT_SECONDS,
    pool=1.0,
)

LIMITS = httpx.Limits(
    max_connections=100,
    max_keepalive_connections=20,
    keepalive_expiry=30.0,
)

_client = httpx.AsyncClient(timeout=TIMEOUT, limits=LIMITS)


class SSPClient:
    async def request(self, *, method, url, params=None, json=None, headers=None):
        return await _client.request(
            method=method,
            url=url,
            params=params,
            json=json,
            headers=headers,
        )


ssp_client = SSPClient()
