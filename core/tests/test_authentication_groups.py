import pytest
from django.conf import settings
from django.contrib.auth.models import Group, User

from core.authentication import user_groups_contains_group_names


@pytest.mark.django_db
def test_user_groups_contains_group_names_positive():
    user = User.objects.create(username="testuser")
    group_name = f"{settings.ENVIRONMENT_SLUG}-admin"
    group = Group.objects.create(name=group_name)
    user.groups.add(group)
    assert user_groups_contains_group_names(user, ["admin"]) is True


@pytest.mark.django_db
def test_user_groups_contains_group_names_negative():
    user = User.objects.create(username="testuser")
    Group.objects.create(name=f"{settings.ENVIRONMENT_SLUG}-other")
    assert user_groups_contains_group_names(user, ["admin"]) is False


@pytest.mark.django_db
def test_user_groups_contains_group_names_multiple():
    user = User.objects.create(username="testuser")
    group1 = Group.objects.create(name=f"{settings.ENVIRONMENT_SLUG}-admin")
    group2 = Group.objects.create(name=f"{settings.ENVIRONMENT_SLUG}-editor")
    user.groups.add(group1, group2)
    assert user_groups_contains_group_names(user, ["admin", "other"]) is True
    assert user_groups_contains_group_names(user, ["other", "editor"]) is True


@pytest.mark.django_db
def test_user_groups_contains_group_names_empty_list():
    user = User.objects.create(username="testuser")
    assert user_groups_contains_group_names(user, []) is False
