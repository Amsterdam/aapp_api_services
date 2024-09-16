import functools
import logging

import jwt
from django.conf import settings
from django.http.response import HttpResponse, JsonResponse
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


ENTRA_ID_JWKS_URI = f"https://login.microsoftonline.com/{settings.TENANT_ID}/discovery/v2.0/keys?appid={settings.CLIENT_ID}"

class IsAuthorized:
    """This class is a decorator for APIs specific for project managers to validate their entra id tokens.

    Usage:

    @isAuthorized
    def example(request):
        <method body>
    """

    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func

    def __call__(self, *args, **kwargs):
        try:
            request = args[0]

            authorization_header = request.headers.get("Authorization")
            if not authorization_header:
                return JsonResponse({'error': 'Authorization header is missing'}, status=401)

            if not authorization_header.startswith('Bearer ') or len(authorization_header.split(' ')) != 2:
                return JsonResponse({'error': 'Invalid Authorization header'}, status=401)

            token = authorization_header.split(' ')[1]
            
            signing_key = self.get_signing_key(token)
            is_valid_token, data = self.validate_token_data(signing_key, token)
            if not is_valid_token:
                return JsonResponse(data, status=403)
            
            if not self.validate_scope(data):
                return JsonResponse({'error': 'Insufficient scope'}, status=403)
            
            return self.func(*args, **kwargs)
        except Exception as error:
            return HttpResponse(f"Server error: {error}", status=500)
    
    def get_signing_key(self, token):
        jwks_client = jwt.PyJWKClient(ENTRA_ID_JWKS_URI)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return signing_key.key    

    def validate_token_data(self, signing_key, token):
        try:
            data = jwt.decode(
                token, 
                signing_key, 
                verify=True,
                algorithms=["RS256"],
                audience=f"api://{settings.CLIENT_ID}",
                issuer=f"https://sts.windows.net/{settings.TENANT_ID}/"
            )
            return True, data
        except ExpiredSignatureError:
            log.info("Token has expired")
            return False, {'error': 'Token has expired'}
        except InvalidSignatureError:
            log.info("Token has invalid signature")
            return False, {'error': 'Token has invalid signature'}
        except Exception as error:
            log.info(f"Error validating token: {error}")
            return False, {'error': 'Error validating token'}

    def validate_scope(self, data):
        if data.get("scp") == "Modules.Edit":
            return True
        return False
