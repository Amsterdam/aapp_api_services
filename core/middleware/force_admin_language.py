from __future__ import annotations

from django.utils import translation


def force_admin_language_middleware(get_response):
    def middleware(request):
        if "/admin" in request.path:
            request.LANGUAGE_CODE = "nl-NL"
            with translation.override("nl-NL"):
                return get_response(request)

        return get_response(request)

    return middleware
