import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

from news.enums.news_article import NewsArticleSource
from news.etl.extract_data import IproxFetcher

logger = logging.getLogger(__name__)

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/news/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "list/amsterdam/")
IPROX_DETAIL_URL = urljoin(IPROX_URL, "item/")
NEWS_ARTICLE_TYPES = NewsArticleSource.choices_as_list()

iprox_fetcher = IproxFetcher(
    iprox_fetch_url=IPROX_ARTICLES_URL,
    iprox_detail_url=IPROX_DETAIL_URL,
    sources=NEWS_ARTICLE_TYPES,
    max_concurrent_requests=20,
)


class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):

        extracted_data = iprox_fetcher.extract()
        if not extracted_data:
            logger.info("No articles found. Ending ETL process.")
            return

        logger.info(
            f"Now we continue with the transform and load steps for {len(extracted_data)} news articles."
        )
