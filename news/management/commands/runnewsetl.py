import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from news.etl.extract_data import get_all_drupal_news
from news.etl.load_data import NewsArticleLoader, garbage_collect_unseen_articles
from news.etl.transform_data import transform

logger = logging.getLogger(__name__)

data_loader = NewsArticleLoader()


class Command(BaseCommand):
    """Upsert news articles"""

    help = "Upsert news articles"

    def handle(self, *args, **kwargs):

        extracted_data = get_all_drupal_news()
        if not extracted_data:
            logger.info("No articles found. Ending ETL process.")
            return

        transformed_data = transform(extracted_data)
        if not transformed_data:
            logger.info("No valid transformed articles found. Ending ETL process.")
            return

        created_articles = data_loader.load(transformed_data)

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

        logger.info("ETL process completed successfully.")
