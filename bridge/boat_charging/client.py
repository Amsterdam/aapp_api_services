import httpx

TIMEOUT = httpx.Timeout(
    connect=5.0,
    read=10,
    write=10,
    pool=5.0,
)

LIMITS = httpx.Limits(
    max_connections=150,
    max_keepalive_connections=50,
    keepalive_expiry=30.0,
)

_client = httpx.AsyncClient(timeout=TIMEOUT, limits=LIMITS)


class Client:
    async def request(self, *, method, url, params=None, json=None, headers=None):
        return await _client.request(
            method=method,
            url=url,
            params=params,
            json=json,
            headers=headers,
        )


client = Client()
