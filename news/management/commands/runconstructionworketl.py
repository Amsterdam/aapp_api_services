import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

from news.etl.extract_data import IproxConstructionWorkFetcher
from news.etl.load_articles import NewsArticleLoader, garbage_collect_unseen_articles
from news.etl.transform_articles import transform_articles

logger = logging.getLogger(__name__)

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/construction-work/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "articles/")
IPROX_PROJECTS_URL = urljoin(IPROX_URL, "projects/")

iprox_fetcher = IproxConstructionWorkFetcher()
article_data_loader = NewsArticleLoader()


class ConstructionWorkETLError(Exception):
    pass


class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):
        try:
            self.projects_etl_run()
            self.articles_etl_run()
        except ConstructionWorkETLError as e:
            logger.error(
                "Construction work ETL process terminated prematurely", exc_info=e
            )

        logger.info("ETL process completed successfully.")

    def projects_etl_run(self):
        projects_data = iprox_fetcher.extract(IPROX_PROJECTS_URL)
        if not projects_data:
            raise ConstructionWorkETLError("No projects found. Ending ETL process.")

    def articles_etl_run(self):
        articles_data = iprox_fetcher.extract(IPROX_ARTICLES_URL)
        if not articles_data:
            raise ConstructionWorkETLError("No articles found. Ending ETL process.")

        transformed_articles_data = transform_articles(articles_data)
        if not transformed_articles_data:
            raise ConstructionWorkETLError(
                "No valid transformed articles found. Ending ETL process."
            )

        created_articles = article_data_loader.load(transformed_articles_data)

        # only delete unseen articles if there were new articles created, otherwise we
        # might end up in a situation where we delete all articles because no new articles are created
        if created_articles and settings.DELETE_UNSEEN_ARTICLES:
            deleted_count = garbage_collect_unseen_articles(
                threshold_seconds=settings.DELETE_UNSEEN_ARTICLES_AFTER_SECONDS
            )
            logger.info(
                "News garbage collector completed.",
                extra={"deleted_count": deleted_count},
            )
        else:
            logger.info("News garbage collector skipped because it is disabled.")
