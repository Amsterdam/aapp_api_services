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


def with_read_timeout(read_timeout: float) -> httpx.Timeout:
    return httpx.Timeout(
        connect=TIMEOUT.connect,
        read=read_timeout,
        write=TIMEOUT.write,
        pool=TIMEOUT.pool,
    )


_client = httpx.AsyncClient(timeout=TIMEOUT, limits=LIMITS)


class Client:
    async def request(self, **kwargs):
        return await _client.request(**kwargs)


client = Client()
