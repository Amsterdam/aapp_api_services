import logging
from copy import deepcopy

from django.core.management.base import BaseCommand
from django.db import connection

from news.etl.load_data import NewsArticleLoader
from news.etl.transform_data import transform
from news.models import NewsArticle
from news.tests.mock_data import item_article, item_liveblog

logger = logging.getLogger(__name__)

FULL_DATASET = [
    {**item_article.MOCK_RESPONSE_123123, **{"type": "article", "district": None}},
    {**item_article.MOCK_RESPONSE_123124, **{"type": "article", "district": None}},
    {**item_article.MOCK_RESPONSE_100000, **{"type": "highlight", "district": None}},
    {**item_liveblog.MOCK_RESPONSE_1234123, **{"type": "liveblog", "district": None}},
    {**item_liveblog.MOCK_RESPONSE_1321235, **{"type": "liveblog", "district": None}},
    {**item_liveblog.MOCK_RESPONSE_1000001, **{"type": "liveblog", "district": None}},
]


class Command(BaseCommand):
    """Inject test data for news articles"""

    help = "Inject deterministic mock data for news articles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-news",
            action="store_true",
            help="Delete existing news records before injecting mock data.",
        )
        parser.add_argument(
            "--without-images",
            action="store_true",
            help="Remove image URLs so loader does not upsert images.",
        )
        parser.add_argument(
            "--with-liveblog-notification",
            action="store_true",
            help="Allow active liveblog notification creation.",
        )

    def handle(self, *args, **kwargs):

        extracted_data = deepcopy(FULL_DATASET)
        reset_news = kwargs["reset_news"]
        without_images = kwargs["without_images"]
        with_liveblog_notification = kwargs["with_liveblog_notification"]

        if reset_news:
            deleted, _ = NewsArticle.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Reset existing news rows: {deleted}")
            )

        if without_images:
            self._strip_images(extracted_data)

        if not with_liveblog_notification:
            for article in extracted_data:
                article["is_active_liveblog"] = False

        transformed_data = transform(extracted_data)

        self._sync_newsarticle_pk_sequence()

        if without_images:
            self._strip_transformed_liveblog_images(transformed_data)

        logger.info(
            f"Now we continue with the load steps for {len(transformed_data)} news articles."
        )

        data_loader = NewsArticleLoader()
        data_loader.load(transformed_data)

        self.stdout.write(
            self.style.SUCCESS(f"Injected {len(transformed_data)} records from dataset")
        )
        logger.info("ETL process completed successfully.")

    def _sync_newsarticle_pk_sequence(self):
        """
        Keep the PostgreSQL auto-increment sequence aligned with existing rows.
        This prevents duplicate PK insert attempts after manual DB inserts.
        """
        if connection.vendor != "postgresql":
            return

        db_table = NewsArticle._meta.db_table
        quoted_table = connection.ops.quote_name(db_table)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence(%s, %s),
                    COALESCE(MAX(id), 1),
                    MAX(id) IS NOT NULL
                )
                FROM {quoted_table}
                """,
                [db_table, "id"],
            )

    def _strip_images(self, extracted_data: list[dict]):
        for article in extracted_data:
            # remove image_url key from article dict
            article.pop("image_url", None)

    def _strip_transformed_liveblog_images(self, transformed_data: list[dict]):
        for article in transformed_data:
            if article.get("type") != "liveblog":
                continue
            for message in article.get("body", []):
                message["image_url"] = None
