import logging

import jwt
from django.conf import Settings, settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

logger = logging.getLogger(__name__)


class EntraIDAuthentication(BaseAuthentication):
    """
    Custom authentication class for Entra ID tokens.

    Since `.authenticate_header()` is not overridden (because "WWW-Authenticate" is not used),
    the authentication scheme will return HTTP 403 Forbidden responses when an unauthenticated request is denied access.
    Regardless of what status code the exception specifies.
    E.g. AuthenticationFailed specifies a status code of 401, but a 403 will be returned.

    Based on the offical documenation: https://www.django-rest-framework.org/api-guide/authentication/
    """

    def authenticate(self, request):
        bearer_token = request.headers.get("Authorization")
        if not bearer_token:
            raise AuthenticationFailed("Missing header")

        if not bearer_token.startswith("Bearer "):
            raise AuthenticationFailed("Missing bearer token")

        token = bearer_token.split(" ")[1]
        try:
            signing_key = self._get_signing_key(token)
            is_valid_token, token_data = self._validate_token_data(signing_key, token)
            if not is_valid_token:
                logger.warning(f"Invalid token: {token_data=}]")
                raise AuthenticationFailed("Invalid token")

            if not self._validate_scope(token_data):
                raise PermissionDenied("Insufficient scope")

            return (None, token_data)

        except jwt.exceptions.DecodeError as error:
            logger.warning(f"Error decoding token: {error}")
            raise AuthenticationFailed("Invalid token")
        except Exception as error:
            logger.warning(f"Authentication error: {error}")
            raise AuthenticationFailed("Authentication failed")

    def _get_signing_key(self, token):
        from jwt import PyJWKClient

        jwks_client = PyJWKClient(Settings.ENTRA_ID_JWKS_URI)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return signing_key.key

    def _validate_token_data(self, signing_key, token):
        try:
            data = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=f"api://{settings.ENTRA_CLIENT_ID}",
                issuer=f"https://sts.windows.net/{settings.ENTRA_TENANT_ID}/",
            )
            return True, data
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return False, {"error": "Token has expired"}
        except jwt.InvalidSignatureError:
            logger.warning("Token has invalid signature")
            return False, {"error": "Token has invalid signature"}
        except Exception as error:
            logger.warning(f"Error validating token: {error}")
            return False, {"error": "Error validating token"}

    def _validate_scope(self, data):
        return data.get("scp") == "Modules.Edit"
