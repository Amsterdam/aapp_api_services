from unittest.mock import patch

import jwt
import responses
import respx
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView

from core.authentication import (
    AbstractAppAuthentication,
    APIKeyAuthentication,
    EntraCookieTokenAuthentication,
    EntraTokenMixin,
    OIDCAuthenticationBackend,
)
from core.utils.patch_utils import (
    apply_signing_key_patch,
    create_jwt_token,
    mock_public_key,
)


class AuthenticatedAPITestCase(APITestCase):
    authentication_class: AbstractAppAuthentication = None
    databases = set(d for d in settings.DATABASES.keys())

    def setUp(self) -> None:
        if self.authentication_class is None:
            raise NotImplementedError("You must specify an authentication_class")

        # Instantiate the authentication class
        auth_instance = self.authentication_class()

        # Prepare API key for authentication
        api_keys = auth_instance.api_keys
        self.api_headers = {auth_instance.api_key_header: api_keys[0]}

        # flush cache before every test run
        cache.clear()

    def assertEqual(self, first, second, msg=None):
        """The 'expected' and 'actual' values are swapped in the assertion."""
        return super().assertEqual(second, first, msg)


@override_settings(
    STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
)
class BasicAPITestCase(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def assert_caching(self, url, rsp_get, request_body=None):
        # First call
        response = self.client.get(url, request_body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(cache.keys("*")), 2
        )  # The request and the headers are cached both as separate keys
        self.assertEqual(rsp_get.call_count, 1)

        # Second call
        response = self.client.get(url, request_body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cache.keys("*")), 2)
        self.assertEqual(
            rsp_get.call_count, 1
        )  # The request should not be called a second time!


class ResponsesActivatedAPITestCase(BasicAPITestCase):
    @responses.activate
    def run(self, result=None):
        # this wraps setUp, each test, and tearDown
        super().run(result)


class RespxActivatedAPITestCase(BasicAPITestCase):
    @respx.mock
    def run(self, result=None):
        # this wraps setUp, each test, and tearDown
        super().run(result)


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


class TestEntraTokenMixin(APITestCase):
    def setUp(self):
        super().setUp()
        self.mixin = EntraTokenMixin()
        self.signing_key_patcher = apply_signing_key_patch(self)

    def tearDown(self):
        self.signing_key_patcher.stop()

    def test_validate_token_success(self):
        """Test successful token validation with correct scope"""
        token = create_jwt_token(
            email="test@test.com",
            first_name="Test",
            last_name="User",
        )
        token_data = self.mixin.validate_token(token)

        self.assertEqual(token_data["upn"], "test@test.com")
        self.assertEqual(token_data["name"], "User, Test")

    def test_validate_token_signing_key_error(self):
        """Test token validation fails when signing key retrieval fails"""
        self.mock_get_signing_key.side_effect = Exception("Mocked error!")
        token = create_jwt_token()

        with self.assertRaises(AuthenticationFailed) as context:
            self.mixin.validate_token(token)

        self.assertEqual(str(context.exception), "Authentication failed")

    def test_validate_token_expired(self):
        """Test token validation fails with expired token"""
        # Create an expired token by mocking the decode method
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.ExpiredSignatureError()
            token = create_jwt_token()

            with self.assertRaises(AuthenticationFailed) as context:
                self.mixin.validate_token(token)

            self.assertEqual(str(context.exception), "Invalid token")

    def test_validate_token_invalid_signature(self):
        """Test token validation fails with invalid signature"""
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.InvalidSignatureError()
            token = create_jwt_token()

            with self.assertRaises(AuthenticationFailed) as context:
                self.mixin.validate_token(token)

            self.assertEqual(str(context.exception), "Invalid token")

    def test_validate_token_general_error(self):
        """Test token validation fails with general error"""
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = Exception("General error")
            token = create_jwt_token()

            with self.assertRaises(AuthenticationFailed) as context:
                self.mixin.validate_token(token)

            self.assertEqual(str(context.exception), "Invalid token")

    def test_get_signing_key_success(self):
        """Test successful signing key retrieval"""
        token = create_jwt_token()
        signing_key = self.mixin._get_signing_key(token)
        self.assertEqual(signing_key, mock_public_key)

    def test_validate_token_data_success(self):
        """Test successful token data validation"""
        token = create_jwt_token()
        is_valid, token_data = self.mixin._validate_token_data(mock_public_key, token)

        self.assertTrue(is_valid)
        self.assertEqual(token_data["aud"], f"api://{settings.ENTRA_CLIENT_ID}")
        self.assertEqual(
            token_data["iss"], f"https://sts.windows.net/{settings.ENTRA_TENANT_ID}/"
        )


class DummyCookieView(APIView):
    authentication_classes = [EntraCookieTokenAuthentication]

    def get(self, request):
        return Response("ok", status=200)


class TestEntraCookieTokenAuthentication(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.factory = APIRequestFactory()
        self.signing_key_patcher = apply_signing_key_patch(self)

    def tearDown(self):
        self.signing_key_patcher.stop()

    def test_successful_authentication(self):
        token = create_jwt_token(
            email="test@test.com", first_name="Test", last_name="Test"
        )
        headers = {"Cookie": f"{settings.ENTRA_TOKEN_COOKIE_NAME}={token}"}

        request = self.factory.get("/", headers=headers)
        response = DummyCookieView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "ok")

    def test_successful_authentication_cookie_chunks(self):
        token = create_jwt_token(
            email="test@test.com", first_name="Test", last_name="Test"
        )
        # Simulate cookie being split into chunks
        token_chunks = [token[i : i + 100] for i in range(0, len(token), 100)]
        token = "; ".join(
            [
                f"{settings.ENTRA_TOKEN_COOKIE_NAME}.{i}={chunk}"
                for i, chunk in enumerate(token_chunks)
            ]
        )
        headers = {"Cookie": token}

        request = self.factory.get("/", headers=headers)
        response = DummyCookieView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "ok")

    def test_missing_cookie(self):
        request = self.factory.get("/")
        response = DummyCookieView.as_view()(request)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Cookie not found", status_code=403)

    def test_superuser_is_created_if_not_exists(self):
        token = create_jwt_token(
            email="test@test.com", first_name="Foo", last_name="Bar"
        )
        headers = {"Cookie": f"{settings.ENTRA_TOKEN_COOKIE_NAME}={token}"}
        request = self.factory.get("/", headers=headers)
        response = DummyCookieView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "ok")
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.first().is_superuser)
        self.assertEqual(User.objects.first().email, "test@test.com")
        self.assertEqual(User.objects.first().username, "test@test.com")
        self.assertEqual(User.objects.first().first_name, "Foo")
        self.assertEqual(User.objects.first().last_name, "Bar")

    def test_groups_are_added_to_user(self):
        email = "test@test.com"

        def get_token(roles):
            return create_jwt_token(
                email=email, first_name="Test", last_name="Test", roles=roles
            )

        def make_request(token):
            headers = {"Cookie": f"{settings.ENTRA_TOKEN_COOKIE_NAME}={token}"}
            request = self.factory.get("/", headers=headers)
            response = DummyCookieView.as_view()(request)
            self.assertEqual(response.status_code, 200)

        def assert_user_has_groups(groups):
            user = User.objects.get(email=email)
            self.assertEqual([group.name for group in user.groups.all()], groups)

        # First user has one group
        roles = ["group1"]
        make_request(get_token(roles))
        assert_user_has_groups(roles)

        # Then same user has extra group
        roles.append("group2")
        make_request(get_token(roles))
        assert_user_has_groups(roles)

        # Then user loses first group
        roles.remove("group1")
        make_request(get_token(roles))
        assert_user_has_groups(roles)


class TestOIDCAuthenticationBackend(TestCase):
    def setUp(self):
        self.backend = OIDCAuthenticationBackend()
        self.sample_claims = {
            "upn": "test.user@amsterdam.nl",
            "given_name": "Test",
            "family_name": "User",
            "roles": ["mbs-admin", "cbs-time-publisher"],
        }

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    @patch("core.authentication.default_username_algo")
    def test_create_user_new_user(self, mock_algo):
        """Test creating a new user with claims"""
        mock_algo.return_value = "test.user@amsterdam.nl"

        user = self.backend.create_user(self.sample_claims)

        # Verify user was created with correct attributes
        self.assertEqual(user.email, "test.user@amsterdam.nl")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        # Verify groups were created and assigned
        self.assertEqual(user.groups.count(), 2)
        group_names = list(user.groups.values_list("name", flat=True))
        self.assertIn("mbs-admin", group_names)
        self.assertIn("cbs-time-publisher", group_names)

    @patch("core.authentication.default_username_algo")
    def test_create_user_existing_user(self, mock_algo):
        """Test updating an existing user with new claims"""
        existing_user = User.objects.create_user(
            username="test.user@amsterdam.nl",
            email="test.user@amsterdam.nl",
            first_name="Old",
            last_name="Name",
            is_staff=False,
            is_superuser=False,
        )

        mock_algo.return_value = "test.user@amsterdam.nl"

        user = self.backend.create_user(self.sample_claims)

        # Verify user was updated, not created
        self.assertEqual(user.id, existing_user.id)
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    @patch("core.authentication.default_username_algo")
    def test_create_user_no_roles(self, mock_algo):
        """Test creating user with no roles in claims"""
        claims_without_roles = {
            "upn": "test.user@amsterdam.nl",
            "given_name": "Test",
            "family_name": "User",
        }

        mock_algo.return_value = "test.user@amsterdam.nl"

        user = self.backend.create_user(claims_without_roles)

        # Verify user was created but has no groups
        self.assertEqual(user.email, "test.user@amsterdam.nl")
        self.assertEqual(user.groups.count(), 0)

    @patch("core.authentication.default_username_algo")
    def test_create_user_empty_roles(self, mock_algo):
        """Test creating user with empty roles list"""
        claims_with_empty_roles = {
            "upn": "test.user@amsterdam.nl",
            "given_name": "Test",
            "family_name": "User",
            "roles": [],
        }

        mock_algo.return_value = "test.user@amsterdam.nl"

        user = self.backend.create_user(claims_with_empty_roles)

        # Verify user was created but has no groups
        self.assertEqual(user.email, "test.user@amsterdam.nl")
        self.assertEqual(user.groups.count(), 0)

    @patch("core.authentication.default_username_algo")
    def test_create_user_missing_fields(self, mock_algo):
        """Test creating user with missing optional fields"""
        minimal_claims = {"upn": "test.user@amsterdam.nl"}

        mock_algo.return_value = "test.user@amsterdam.nl"

        self.assertRaises(IntegrityError, self.backend.create_user, minimal_claims)

    @patch("core.authentication.default_username_algo")
    def test_update_user_groups_clears_existing_groups(self, _):
        """Test that _update_user_groups clears existing groups before adding new ones"""
        user = User.objects.create_user(
            username="test.user@amsterdam.nl", email="test.user@amsterdam.nl"
        )
        old_group = Group.objects.create(name="old-group")
        user.groups.add(old_group)

        # Update with new roles
        self.backend._update_user_groups(user, {"roles": ["new-role"]})

        # Verify old group was removed and new group was added
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, "new-role")

    @patch("core.authentication.default_username_algo")
    def test_update_user_groups_creates_groups_if_not_exist(self, _):
        """Test that _update_user_groups creates groups if they don't exist"""
        user = User.objects.create_user(
            username="test.user@amsterdam.nl", email="test.user@amsterdam.nl"
        )

        # Update with roles that don't exist yet
        self.backend._update_user_groups(
            user, {"roles": ["new-group-1", "new-group-2"]}
        )

        # Verify groups were created and assigned
        self.assertEqual(user.groups.count(), 2)
        group_names = list(user.groups.values_list("name", flat=True))
        self.assertIn("new-group-1", group_names)
        self.assertIn("new-group-2", group_names)

    @patch("core.authentication.default_username_algo")
    @patch("core.authentication.Group.objects.get_or_create")
    def test_update_user_groups_transaction_rollback(self, _, mock_get_or_create):
        """Test that _update_user_groups uses transaction and can rollback on error"""
        user = User.objects.create_user(
            username="test.user@amsterdam.nl", email="test.user@amsterdam.nl"
        )

        # Mock Group.objects.get_or_create to raise an exception
        mock_get_or_create.side_effect = Exception("Database error")

        # This should raise an exception and rollback any changes
        with self.assertRaises(Exception):
            self.backend._update_user_groups(user, {"roles": ["test-role"]})

        # Verify no groups were created or assigned
        self.assertEqual(Group.objects.count(), 0)
        self.assertEqual(user.groups.count(), 0)
