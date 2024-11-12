import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from core.authentication import APIKeyAuthentication
from notification.models import Client


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_url():
    return reverse("notification-register-client")


@pytest.fixture
def api_headers():
    # Mimic the behavior of AuthenticatedAPITestCase
    auth_instance = APIKeyAuthentication()
    api_keys = auth_instance.api_keys
    return {auth_instance.api_key_header: api_keys[0]}


@pytest.mark.django_db
def test_registration_ok(api_client, api_url, api_headers):
    """Test registering a new client"""
    data = {"firebase_token": "foobar_token", "os": "ios"}
    api_headers[settings.HEADER_CLIENT_ID] = "0"
    first_result = api_client.post(api_url, data, headers=api_headers)

    assert first_result.status_code == 200
    assert first_result.data.get("firebase_token") == data.get("firebase_token")
    assert first_result.data.get("os") == data.get("os")

    # Silent discard second call
    second_result = api_client.post(api_url, data, headers=api_headers)

    assert second_result.status_code == 200
    assert second_result.data.get("firebase_token") == data.get("firebase_token")
    assert second_result.data.get("os") == data.get("os")

    # Assert only one record in db
    clients_with_token = list(Client.objects.filter(firebase_token__isnull=False).all())
    assert len(clients_with_token) == 1


@pytest.mark.django_db
def test_delete_registration(api_client, api_url, api_headers):
    """Test removing a client registration"""
    new_client = Client(
        external_id="foobar_client", firebase_token="foobar_token", os="os"
    )
    new_client.save()

    # Delete registration
    api_headers[settings.HEADER_CLIENT_ID] = "foobar_client"
    first_result = api_client.delete(api_url, headers=api_headers)

    assert first_result.status_code == 200
    assert first_result.data == "Registration removed"

    # Expect no records in db
    clients_with_token = list(Client.objects.filter(firebase_token__isnull=False).all())
    assert len(clients_with_token) == 0

    # Silently discard not existing registration delete
    second_result = api_client.delete(api_url, headers=api_headers)

    assert second_result.status_code == 200
    assert second_result.data == "Registration removed"


@pytest.mark.django_db
def test_delete_no_client(api_client, api_url, api_headers):
    api_headers[settings.HEADER_CLIENT_ID] = "non-existing-client-id"
    first_result = api_client.delete(api_url, headers=api_headers)

    assert first_result.status_code == 200


@pytest.mark.django_db
def test_missing_os_missing(api_client, api_url, api_headers):
    """Test if missing OS is detected"""
    data = {"firebase_token": "0"}
    api_headers[settings.HEADER_CLIENT_ID] = "foobar"
    result = api_client.post(api_url, data, headers=api_headers)

    assert result.status_code == 400


@pytest.mark.django_db
def test_missing_firebase_token(api_client, api_url, api_headers):
    """Test if missing token is detected"""
    data = {"os": "ios"}
    api_headers[settings.HEADER_CLIENT_ID] = "foobar"
    result = api_client.post(api_url, data, headers=api_headers)

    assert result.status_code == 400


@pytest.mark.django_db
def test_missing_client_id(api_client, api_url, api_headers):
    """Test if missing client identifier is detected"""
    data = {"firebase_token": "0", "os": "ios"}
    result = api_client.post(api_url, data, headers=api_headers)

    assert result.status_code == 400
