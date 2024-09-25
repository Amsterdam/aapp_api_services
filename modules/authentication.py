import logging

from azure_ad_verify_token import verify_jwt
from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class BearerAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "modules.authentication.AzureAdVerifyJWTAuthentication"
    name = "Azure AD Token"

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="Authorization", token_prefix="Bearer", bearer_format="JWT"
        )


class AzureAdVerifyJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication using `azure-ad-verify-token` for Azure Entra ID.
    """

    def get_validated_token(self, raw_token):
        try:
            valid_audiences = [
                f"api://{settings.CLIENT_ID}"
            ]  # Your Azure AD app client ID
            jwks_uri = f"https://login.microsoftonline.com/{settings.TENANT_ID}/discovery/v2.0/keys"
            issuer = f"https://sts.windows.net/{settings.TENANT_ID}/"

            validated_token = verify_jwt(
                token=raw_token,
                tenant_id=settings.TENANT_ID,
                app_id=settings.CLIENT_ID,
                valid_audiences=valid_audiences,
                jwks_uri=jwks_uri,
                issuer=issuer,
            )
            return validated_token
        except Exception as e:
            raise InvalidToken(f"Token validation error: {str(e)}")

    def get_user(self, validated_token):
        scp_claim = validated_token.get("scp")
        if scp_claim and "Modules.Edit" in scp_claim:
            unique_name = validated_token.get("unique_name")
            if not unique_name:
                raise InvalidToken("Token does not contain unique_name.")

            # Instead of fetching a User instance, return a SimpleUser instance
            return SimpleUser(username=unique_name)
        else:
            raise InvalidToken("Token does not have required scope.")


class SimpleUser:
    def __init__(self, username):
        self.username = username
        self.is_authenticated = True
