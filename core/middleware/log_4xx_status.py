import logging
from asyncio import iscoroutinefunction

from django.utils.decorators import sync_and_async_middleware

logger = logging.getLogger(__name__)


@sync_and_async_middleware
def log_4xx_middleware(get_response):
    max_body_len = 200

    async def _async(request):
        response = await get_response(request)
        status = getattr(response, "status_code", None)

        if status is not None and 400 <= status < 500:
            try:
                release_version = request.headers.get("releaseVersion")
                extra = {"releaseVersion": release_version} if release_version else None

                body = ""
                # Don’t consume streaming responses
                if hasattr(response, "content"):
                    body = response.content.decode(errors="replace")[:max_body_len]

                logger.warning(
                    f"{request.method} {request.get_full_path()} → {status}: {body}",
                    extra=extra,
                )
            except Exception as e:
                logger.error(
                    f"Error logging 4xx response: {e}",
                    extra={
                        "request_method": request.method,
                        "request_path": request.get_full_path(),
                    },
                )
        return response

    def _sync(request):
        response = get_response(request)
        status = getattr(response, "status_code", None)

        if status is not None and 400 <= status < 500:
            try:
                release_version = request.headers.get("releaseVersion")
                extra = {"releaseVersion": release_version} if release_version else None

                body = ""
                if hasattr(response, "content"):
                    body = response.content.decode(errors="replace")[:max_body_len]

                logger.warning(
                    f"{request.method} {request.get_full_path()} → {status}: {body}",
                    extra=extra,
                )
            except Exception as e:
                logger.error(
                    f"Error logging 4xx response: {e}",
                    extra={
                        "request_method": request.method,
                        "request_path": request.get_full_path(),
                    },
                )
        return response

    return _async if iscoroutinefunction(get_response) else _sync
