from django.core.management.base import BaseCommand

from construction_work.etl.send_notifications import send_article_notifications
from construction_work.etl.update_data import extract_transform_load, garbage_collector
from construction_work.models.article_models import Article


class Command(BaseCommand):
    """Upsert construction work projects and articles"""

    help = "Upsert construction work projects and articles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--first_run",
            action="store_true",
            help="Run the ETL process without sending notifications and do garbage collection",
        )

    def handle(self, *args, **kwargs):

        if not kwargs.get("first_run", False):
            current_article_ids = set(
                Article.objects.values_list("drupal_id", flat=True)
            )

        found_projects, found_articles = extract_transform_load()

        if not kwargs.get("first_run", False):
            send_article_notifications(current_article_ids, found_articles)
            garbage_collector(found_projects, found_articles)
