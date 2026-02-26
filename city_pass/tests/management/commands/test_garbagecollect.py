from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone
from model_bakery import baker

from city_pass.models import RefreshToken, Session
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestCommand(ResponsesActivatedAPITestCase):
    def setUp(self, **kwargs):
        self.logged_in_session = baker.make(
            Session, encrypted_adminstration_no="foobar"
        )
        self.session_without_login = baker.make(
            Session, encrypted_adminstration_no=None
        )

    def test_cleanup_sessions_without_login(self):
        baker.make(Session, encrypted_adminstration_no=None, _quantity=5)

        call_command("garbagecollect")

        self.assertEqual(Session.objects.count(), 1)

    def test_cleanup_expired_refresh_tokens(self):
        baker.make(
            RefreshToken,
            expires_at=timezone.now() - timedelta(days=1),
            session=self.logged_in_session,
            _quantity=5,
        )

        call_command("garbagecollect")

        self.assertEqual(RefreshToken.objects.count(), 0)

    def test_cleanup_non_expired_refresh_tokens(self):
        baker.make(
            RefreshToken,
            expires_at=timezone.now() + timedelta(days=1),
            session=self.logged_in_session,
            _quantity=5,
        )
        baker.make(
            RefreshToken, expires_at=None, session=self.logged_in_session, _quantity=5
        )

        call_command("garbagecollect")

        self.assertEqual(RefreshToken.objects.count(), 10)

    def test_cleanup_mixed_refresh_tokens(self):
        baker.make(
            RefreshToken,
            expires_at=timezone.now() - timedelta(days=1),
            session=self.logged_in_session,
            _quantity=5,
        )
        baker.make(
            RefreshToken,
            expires_at=timezone.now() + timedelta(days=1),
            session=self.logged_in_session,
            _quantity=5,
        )
        baker.make(
            RefreshToken, expires_at=None, session=self.logged_in_session, _quantity=5
        )

        call_command("garbagecollect")

        self.assertEqual(RefreshToken.objects.count(), 10)

    def test_cleanup_complex_case(self):
        baker.make(Session, encrypted_adminstration_no=None, _quantity=5)
        baker.make(
            RefreshToken,
            expires_at=timezone.now() - timedelta(days=1),
            session=self.logged_in_session,
            _quantity=5,
        )
        baker.make(
            RefreshToken,
            expires_at=timezone.now() - timedelta(days=1),
            session=self.session_without_login,
            _quantity=5,
        )
        baker.make(
            RefreshToken,
            expires_at=timezone.now() + timedelta(days=1),
            session=self.logged_in_session,
            _quantity=5,
        )
        baker.make(
            RefreshToken,
            expires_at=timezone.now() + timedelta(days=1),
            session=self.session_without_login,
            _quantity=5,
        )

        call_command("garbagecollect")

        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(RefreshToken.objects.count(), 5)
