import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from city_pass.models import RefreshToken, Session

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Garbage collect for city pass tokens."""

    help = "Clean up city pass tokens."

    def handle(self, *args, **kwargs):
        # Remove sessions without admin no. They never completed their login
        Session.objects.filter(encrypted_adminstration_no__isnull=True).delete()

        # Remove expired refresh tokens
        refresh_tokens = RefreshToken.objects.all()
        refresh_tokens = list(
            refresh_tokens
        )  # Evaluate the queryset to avoid multiple queries
        RefreshToken.objects.filter(expires_at__lt=timezone.now()).delete()
