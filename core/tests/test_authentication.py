from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView

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


class ExampleAppAuthentication(AbstractAppAuthentication):
    api_keys = ["test-api-key", "other-api-key"]
    api_key_header = "X-Api-Key"


class ExampleView(APIView):
    authentication_classes = [ExampleAppAuthentication]
    permission_classes = []

    def get(self, request):
        return Response("success")


class TestAbstractAppAuthentication(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.factory = APIRequestFactory()
        self.auth_class = ExampleAppAuthentication

    def test_successful_authentication(self):
        headers = {self.auth_class.api_key_header: self.auth_class.api_keys[0]}
        request = self.factory.get("/", headers=headers)
        response = ExampleView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "success")

    def test_missing_authentication(self):
        request = self.factory.get("/")
        response = ExampleView.as_view()(request)
        self.assertEqual(response.status_code, 401)

    def test_invalid_api_key(self):
        headers = {self.auth_class.api_key_header: "invalid-api-key"}
        request = self.factory.get("/", headers=headers)
        response = ExampleView.as_view()(request)
        self.assertEqual(response.status_code, 401)
        self.assertContains(response, "Invalid API key", status_code=401)
