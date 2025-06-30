from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase, override_settings

from core.permissions import AdminPermission


@override_settings(ADMIN_ROLES=["cbs-time-publisher", "cbs-time-delegated"])
class IsTimeAdminPermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = AdminPermission()
        self.time_publisher = Group.objects.create(name="o-cbs-time-publisher")
        self.time_delegated = Group.objects.create(name="o-cbs-time-delegated")

    def test_has_permission_success_delegated(self):
        user = User.objects.create(username="testuser")
        user.groups.add(self.time_delegated)

        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_has_permission_success_publisher(self):
        user = User.objects.create(username="testuser")
        user.groups.add(self.time_publisher)

        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_user_not_in_group(self):
        user = User.objects.create(username="testuser")
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_group_does_not_exist(self):
        self.time_delegated.delete()
        self.time_publisher.delete()
        user = User.objects.create(username="testuser")
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    @override_settings(ENVIRONMENT_SLUG="a")
    def test_roles_different_environment(self):
        user = User.objects.create(username="testuser")
        user.groups.add(self.time_publisher)
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    @override_settings(ENVIRONMENT_SLUG="a")
    def test_roles_environments_constructed_correctly(self):
        user = User.objects.create(username="testuser")
        group = Group.objects.create(name="a-cbs-time-publisher")
        user.groups.add(group)
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))
