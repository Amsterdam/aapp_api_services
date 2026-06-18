import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

from news.enums.news_article import NewsArticleSource
from news.etl.extract_data import IproxNewsFetcher
from news.etl.load_articles import NewsArticleLoader, garbage_collect_unseen_articles
from news.etl.transform_articles import transform_articles
from news.management.commands._stage_runner import (
    ETLStageAborted,
    maybe_garbage_collect,
    run_stage,
)

logger = logging.getLogger(__name__)

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/news/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "list/amsterdam/")
IPROX_DETAIL_URL = urljoin(IPROX_URL, "item/")
NEWS_ARTICLE_TYPES = NewsArticleSource.choices_as_list()

iprox_fetcher = IproxNewsFetcher(
    iprox_fetch_url=IPROX_ARTICLES_URL,
    iprox_detail_url=IPROX_DETAIL_URL,
    sources=NEWS_ARTICLE_TYPES,
)

data_loader = NewsArticleLoader()


class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):
        try:
            article_load_result = run_stage(
                extract=iprox_fetcher.extract,
                extract_empty_message="No articles found. Ending ETL process.",
                transform=transform_articles,
                transform_empty_message="No valid transformed articles found. Ending ETL process.",
                load=data_loader.load,
            )
        except ETLStageAborted as error:
            logger.info(str(error))
            return

        maybe_garbage_collect(
            created_records=article_load_result,
            garbage_collect=garbage_collect_unseen_articles,
            enabled=settings.DELETE_UNSEEN_ARTICLES,
            threshold_seconds=settings.DELETE_UNSEEN_ARTICLES_AFTER_SECONDS,
            logger=logger,
        )

        logger.info("ETL process completed successfully.")
