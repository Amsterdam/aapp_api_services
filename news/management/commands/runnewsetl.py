import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):
        
        # extract all news articles
        logger.info("Extracting news articles from source")


