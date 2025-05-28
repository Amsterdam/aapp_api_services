from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, override_settings

from contact.views.admin_views import CustomAdminLoginView
from core.tests.test_authentication import ResponsesActivatedAPITestCase


@override_settings(CBS_TIME_PUBLISHER_GROUP="entra_admin")
class TestContactAdminLoginView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()

        self.view_class = CustomAdminLoginView
        self.factory = RequestFactory()
        self.admin_group = Group.objects.create(name="entra_admin")
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.test_user.groups.add(self.admin_group)

    @patch("contact.views.admin_views.EntraCookieTokenAuthentication")
    @patch("core.views.admin_views.login")
    @patch("core.views.admin_views.reverse")
    @patch("core.views.admin_views.redirect")
    def test_admin_login_view_success(
        self, mock_redirect, mock_reverse, mock_login, mock_auth
    ):
        # Arrange
        request = self.factory.get("/admin/login/")

        mock_auth_instance = mock_auth.return_value
        mock_auth_instance.authenticate.return_value = (self.test_user, None)
        mock_redirect.return_value = MagicMock(status_code=302)
        mock_login.return_value = None
        mock_reverse.return_value = None

        # Act
        response = self.view_class.as_view()(request)

        # Assert
        self.assertEqual(response.status_code, 302)

    @patch("contact.views.admin_views.EntraCookieTokenAuthentication")
    def test_admin_login_view_authentication_failed(self, mock_auth):
        # Arrange
        request = self.factory.get("/admin/login/")
        mock_auth_instance = mock_auth.return_value
        mock_auth_instance.authenticate.return_value = (AnonymousUser(), None)

        # Act & Assert
        with self.assertRaises(PermissionDenied):
            self.view_class.as_view()(request)
        mock_auth_instance.authenticate.assert_called_once_with(request)

    @patch("contact.views.admin_views.EntraCookieTokenAuthentication")
    def test_admin_login_view_insufficient_permissions(self, mock_auth):
        # Arrange
        request = self.factory.get("/admin/login/")
        mock_auth_instance = mock_auth.return_value
        mock_auth_instance.authenticate.return_value = (self.test_user, None)
        self.test_user.groups.remove(self.admin_group)

        # Act & Assert
        with self.assertRaises(PermissionDenied):
            self.view_class.as_view()(request)
        mock_auth_instance.authenticate.assert_called_once_with(request)
