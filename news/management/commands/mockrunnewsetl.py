from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from news.management.commands import runnewsetl


class Command(BaseCommand):
    """Run the news ETL command without requesting external data."""

    help = "Mock run news ETL process"

    def handle(self, *args, **kwargs):
        if settings.ENVIRONMENT == "production":
            self.stderr.write("This command should not be run in production!")
            return

        with patch.object(runnewsetl, "get_all_drupal_news", return_value=[]):
            call_command("runnewsetl")
