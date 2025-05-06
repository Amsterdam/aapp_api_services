import logging

logger = logging.getLogger(__name__)


class Log4xxMiddleware:
    """
    Log every 4xx response with a short body snippet.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        self.max_body_len = 200

    def __call__(self, request):
        response = self.get_response(request)

        status = response.status_code
        if 400 <= status < 500:
            try:
                release_version = request.headers.get("releaseVersion")
                extra = {"releaseVersion": release_version} if release_version else None
                body = response.content.decode(errors="replace")[: self.max_body_len]
                logger.warning(
                    f"{request.method} {request.get_full_path()} → "
                    f"{response.status_code}: {body}",
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
