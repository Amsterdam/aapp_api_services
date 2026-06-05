import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

from news.enums.news_article import NewsArticleSource
from news.etl.extract_data import IproxFetcher
from news.etl.load_data import NewsArticleLoader, garbage_collect_unseen_articles
from news.etl.transform_data import transform

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

data_loader = NewsArticleLoader()


class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):

        extracted_data = iprox_fetcher.extract()
        if not extracted_data:
            logger.info("No articles found. Ending ETL process.")
            return

        transformed_data = transform(extracted_data)
        if not transformed_data:
            logger.info("No valid transformed articles found. Ending ETL process.")
            return

        data_loader.load(transformed_data)

        if settings.DELETE_UNSEEN_ARTICLES:
            deleted_count = garbage_collect_unseen_articles(
                threshold_seconds=settings.DELETE_UNSEEN_ARTICLES_AFTER_SECONDS
            )
            logger.info(
                "News garbage collector completed.",
                extra={"deleted_count": deleted_count},
            )
        else:
            logger.info("News garbage collector skipped because it is disabled.")

        logger.info("ETL process completed successfully.")
