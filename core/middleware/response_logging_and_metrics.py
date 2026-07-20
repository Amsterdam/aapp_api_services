import logging

from asgiref.sync import iscoroutinefunction
from django.utils.decorators import sync_and_async_middleware

from core.metrics import successful_requests_counter

logger = logging.getLogger(__name__)


def _handle_response_metrics_and_4xx_logging(request, response):
    max_body_len = 200
    status = getattr(response, "status_code", None)

    # Metrics: count successful requests
    if status is not None and status < 400:
        try:
            successful_requests_counter.add(
                1,
                {
                    "method": request.method,
                    "path": request.path,
                },
            )
        except Exception:
            # Never break request flow because of metrics
            pass

    # logging for 4xx responses
    if status is not None and 400 <= status < 500:
        try:
            release_version = request.headers.get("releaseVersion")
            extra = {"releaseVersion": release_version} if release_version else {}

            body = ""
            # Don’t consume streaming responses
            if hasattr(response, "content"):
                body = response.content.decode(errors="replace")[:max_body_len]

            logger.warning(
                f"{request.method} {request.path}",
                extra={
                    **extra,
                    "status": status,
                    "method": request.method,
                    "body": body,
                    "full_path": request.get_full_path(),
                },
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


@sync_and_async_middleware
def handle_response_metrics_and_4xx_logging_middleware(get_response):
    async def _async(request):
        response = await get_response(request)
        return _handle_response_metrics_and_4xx_logging(request, response)

    def _sync(request):
        response = get_response(request)
        return _handle_response_metrics_and_4xx_logging(request, response)

    return _async if iscoroutinefunction(get_response) else _sync
