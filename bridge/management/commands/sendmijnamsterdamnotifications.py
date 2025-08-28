from django.core.management.base import BaseCommand

from bridge.mijnamsterdam.processor import MijnAmsterdamNotificationProcessor


class Command(BaseCommand):
    """Send notifications from Mijn Amsterdam."""

    help = "Send notifications from Mijn Amsterdam."

    def handle(self, *args, **kwargs):
        notification_processor = MijnAmsterdamNotificationProcessor()
        notification_processor.run()
