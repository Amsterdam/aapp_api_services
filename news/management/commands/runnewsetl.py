import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

from news.enums.news_article import NewsArticle
from news.etl.extract_data import IproxFetcher

logger = logging.getLogger(__name__)

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/news/amsterdam/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "item/")
NEWS_ARTICLE_TYPES = NewsArticle.choices_as_list()

iprox_fetcher = IproxFetcher(
    iprox_fetch_url=IPROX_URL, iprox_detail_url=IPROX_ARTICLES_URL, sources=NEWS_ARTICLE_TYPES, max_concurrent_requests=20
)

class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):
        
        # extract all news articles
        logger.info("Extracting news articles from source")
        all_iprox_items = iprox_fetcher.fetch_all_items()
        extracted_data = iprox_fetcher.fetch_items_data(
            items=all_iprox_items
        )
        logger.info(f"Extracted {len(extracted_data)} news articles from source")


