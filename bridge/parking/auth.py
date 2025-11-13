from enum import Enum
from functools import wraps

import jwt
from django.conf import settings
from requests import Request
from rest_framework import status
from rest_framework.response import Response


class Role(Enum):
    USER = "ROLE_USER_SSP"
    VISITOR = "ROLE_VISITOR_SSP"


def get_access_token(request, external_api: bool = False):
    """
    Extracts the access token from the request headers.
    If external_api is True, returns the external token; otherwise, returns the internal token.
    """
    tokens = request.headers.get(settings.SSP_ACCESS_TOKEN_HEADER)
    if not tokens:
        return
    tokens = tokens.split("%AMSTERDAMAPP%")
    internal_token = tokens[0]
    external_token = tokens[-1]
    if external_api:
        return external_token
    return internal_token


def get_role(request: Request) -> str | None:
    token = get_access_token(request)  # internal token
    decoded_jwt = jwt.decode(token, options={"verify_signature": False})
    roles = decoded_jwt.get("roles", [])

    if len(roles) == 0:
        return None
    return roles[0]


def check_user_role(allowed_roles: list[Role]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            request = getattr(args[0], "request", None)
            role = get_role(request)
            if not role:
                return Response(
                    data="No roles found in token.", status=status.HTTP_401_UNAUTHORIZED
                )
            if role not in allowed_roles:
                return Response(
                    data=f"{role} doesn't have access.",
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            kwargs["is_visitor"] = role == Role.VISITOR.value
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
