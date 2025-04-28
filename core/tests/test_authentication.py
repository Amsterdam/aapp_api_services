from rest_framework.test import APITestCase

from core.authentication import AbstractAppAuthentication, APIKeyAuthentication


class AuthenticatedAPITestCase(APITestCase):
    authentication_class: AbstractAppAuthentication = None

    def setUp(self) -> None:
        if self.authentication_class is None:
            raise NotImplementedError("You must specify an authentication_class")

        # Instantiate the authentication class
        auth_instance = self.authentication_class()

        # Prepare API key for authentication
        api_keys = auth_instance.api_keys
        self.api_headers = {auth_instance.api_key_header: api_keys[0]}


class BasicAPITestCase(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication
