from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase, override_settings

from contact.permissions import IsTimeAdmin


@override_settings(CBS_TIME_PUBLISHER_GROUP="cbs-time-group")
class IsTimeAdminPermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsTimeAdmin()
        self.time_group = Group.objects.create(name="cbs-time-group")

    def test_has_permission_success(self):
        user = User.objects.create(username="testuser")
        user.groups.add(self.time_group)

        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_user_not_in_group(self):
        user = User.objects.create(username="testuser")
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_group_does_not_exist(self):
        self.time_group.delete()
        user = User.objects.create(username="testuser")
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))
