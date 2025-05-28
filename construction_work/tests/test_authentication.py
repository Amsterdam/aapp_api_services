from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from construction_work.authentication import EntraIDAuthentication
from construction_work.permissions import IsEditor, IsPublisher
from construction_work.utils.patch_utils import (
    create_bearer_token,
)
from core.utils.patch_utils import apply_signing_key_patch


class TestEntraIDAuthentication(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.signing_key_patcher = apply_signing_key_patch(self)

    def tearDown(self):
        self.signing_key_patcher.stop()

    def test_valid_scope_token(self):
        """
        Test that a valid token with correct scope authenticates successfully.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token()
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_missing_auth_header(self):
        """
        Test that missing Authorization header results in 403.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        request = self.factory.post("/")
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_invalid_auth_header(self):
        """
        Test that an invalid Authorization header results in 403.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        headers = {
            # Missing "Bearer " in front of token
            "Authorization": "foobar-token",
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_invalid_token(self):
        """
        Test that an invalid token results in 403.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        headers = {
            "Authorization": "Bearer foobar-token",
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_error_on_get_signing_key(self):
        """
        Test that error on get signing key results in AuthenticationFailed.
        """
        # Simulate DecodeError in _get_signing_key
        self.mock_get_signing_key.side_effect = Exception("Mocked error!")

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token()
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_valid_editor_token(self):
        """
        Test that an editor token grants access to views requiring IsEditor.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]
            permission_classes = [IsEditor]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token(groups=[settings.EDITOR_GROUP_ID])
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "success")

    def test_invalid_editor_group(self):
        """
        Test that a token without editor group denies access to IsEditor views.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]
            permission_classes = [IsEditor]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token(groups=["InvalidGroup"])
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 403)
        self.assertIn("permission_denied", str(response.data).lower())

    def test_publisher_cannot_access_editor_view(self):
        """
        Test that a publisher cannot access views requiring IsEditor.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]
            permission_classes = [IsEditor]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token(groups=[settings.PUBLISHER_GROUP_ID])
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 403)
        self.assertIn("permission_denied", str(response.data).lower())

    def test_valid_publisher_token(self):
        """
        Test that a publisher token grants access to views requiring IsPublisher.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]
            permission_classes = [IsPublisher]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token(groups=[settings.PUBLISHER_GROUP_ID])
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "success")

    def test_invalid_publisher_group(self):
        """
        Test that a token without publisher group denies access to IsPublisher views.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]
            permission_classes = [IsPublisher]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token(groups=["InvalidGroup"])
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 403)
        self.assertIn("permission_denied", str(response.data).lower())

    def test_editor_can_access_publisher_view(self):
        """
        Test that an editor can access views requiring IsPublisher.
        """

        class TestView(APIView):
            authentication_classes = [EntraIDAuthentication]
            permission_classes = [IsPublisher]

            def post(self, request):
                return Response({"message": "success"}, status=status.HTTP_200_OK)

        jwt_token = create_bearer_token(groups=[settings.EDITOR_GROUP_ID])
        headers = {
            "Authorization": jwt_token,
        }
        request = self.factory.post("/", headers=headers)
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "success")
