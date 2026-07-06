import inspect

from aiohttp.abc import AbstractStreamWriter
from aiohttp.client_reqrep import ClientResponse


class _CompatStreamWriter(AbstractStreamWriter):
    async def write(self, chunk):
        return None

    async def write_eof(self, chunk=b""):
        return None

    async def drain(self):
        return None

    def enable_compression(self, encoding="deflate", strategy=0):
        return None

    def enable_chunking(self):
        return None

    async def write_headers(self, status_line, headers):
        return None


def patch_client_response_init() -> None:
    parameters = inspect.signature(ClientResponse.__init__).parameters
    stream_writer = parameters.get("stream_writer")
    if stream_writer is None or stream_writer.default is not inspect.Signature.empty:
        return

    original_init = ClientResponse.__init__

    def _compat_init(self, method, url, **kwargs):
        kwargs.setdefault("stream_writer", _CompatStreamWriter())
        return original_init(self, method, url, **kwargs)

    ClientResponse.__init__ = _compat_init
