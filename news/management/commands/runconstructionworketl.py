import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

from news.etl.extract_data import IproxConstructionWorkFetcher
from news.etl.load_articles import NewsArticleLoader, garbage_collect_unseen_articles
from news.etl.load_projects import projects as load_projects
from news.etl.transform_articles import transform_articles
from news.management.commands._stage_runner import (
    ETLStageAborted,
    maybe_garbage_collect,
    run_stage,
)

logger = logging.getLogger(__name__)

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/construction-work/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "articles/")
IPROX_PROJECTS_URL = urljoin(IPROX_URL, "projects/")

iprox_fetcher = IproxConstructionWorkFetcher()
project_data_loader = load_projects
article_data_loader = NewsArticleLoader()


class ConstructionWorkETLError(Exception):
    pass


class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):
        try:
            run_stage(
                extract=self._extract_projects,
                extract_empty_message="No projects found. Ending ETL process.",
                load=project_data_loader,
            )
            article_load_result = run_stage(
                extract=self._extract_articles,
                extract_empty_message="No articles found. Ending ETL process.",
                transform=transform_articles,
                transform_empty_message="No valid transformed articles found. Ending ETL process.",
                load=article_data_loader.load,
            )
        except ETLStageAborted as error:
            logger.error(
                "Construction work ETL process terminated prematurely",
                exc_info=ConstructionWorkETLError(str(error)),
            )
            return

        maybe_garbage_collect(
            created_records=article_load_result,
            garbage_collect=garbage_collect_unseen_articles,
            enabled=settings.DELETE_UNSEEN_ARTICLES,
            threshold_seconds=settings.DELETE_UNSEEN_ARTICLES_AFTER_SECONDS,
            logger=logger,
        )

        logger.info("ETL process completed successfully.")

    def _extract_projects(self):
        return iprox_fetcher.extract(IPROX_PROJECTS_URL)

    def _extract_articles(self):
        return iprox_fetcher.extract(IPROX_ARTICLES_URL)
