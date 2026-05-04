from __future__ import annotations

from asgiref.sync import iscoroutinefunction
from django.utils import translation
from django.utils.decorators import sync_and_async_middleware


@sync_and_async_middleware
def force_admin_language_middleware(get_response):
    async def _async(request):
        if "/admin" in request.path:
            request.LANGUAGE_CODE = "nl-NL"
            with translation.override("nl-NL"):
                return await get_response(request)

        return await get_response(request)

    def _sync(request):
        if "/admin" in request.path:
            request.LANGUAGE_CODE = "nl-NL"
            with translation.override("nl-NL"):
                return get_response(request)

        return get_response(request)

    return _async if iscoroutinefunction(get_response) else _sync
