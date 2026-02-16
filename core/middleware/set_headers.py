from django.utils.decorators import sync_and_async_middleware


@sync_and_async_middleware
def default_headers_middleware(get_response):
    async def _async(request):
        response = await get_response(request)
        if request.path.endswith(".ics"):
            return response

        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        if response.get("Content-Type"):
            if "charset" not in response["Content-Type"]:
                response["Content-Type"] += "; charset=UTF-8"
        else:
            response["Content-Type"] = "application/json; charset=UTF-8"

        return response

    def _sync(request):
        response = get_response(request)
        if request.path.endswith(".ics"):
            return response

        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        if response.get("Content-Type"):
            if "charset" not in response["Content-Type"]:
                response["Content-Type"] += "; charset=UTF-8"
        else:
            response["Content-Type"] = "application/json; charset=UTF-8"

        return response

    return (
        _async
        if callable(get_response) and getattr(get_response, "_is_coroutine", False)
        else _sync
    )
