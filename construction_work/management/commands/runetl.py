from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from construction_work.etl.send_notifications import send_article_notifications
from construction_work.etl.update_data import extract_transform_load, garbage_collector
from construction_work.models.article_models import Article
from core.utils.dvo_utils import DvORequestError


class Command(BaseCommand):
    """Upsert construction work projects and articles"""

    help = "Upsert construction work projects and articles"

    def handle(self, *args, **kwargs):

        if settings.SEND_ETL_NOTIFICATIONS:
            current_article_ids = set(
                Article.objects.values_list("drupal_id", flat=True)
            )

        try:
            found_projects, found_articles = extract_transform_load()
        except DvORequestError as error:
            raise CommandError(
                "ETL aborted before data was changed because a DvO request failed: "
                f"{error}"
            ) from error

        if settings.SEND_ETL_NOTIFICATIONS:
            send_article_notifications(current_article_ids, found_articles)

        garbage_collector(found_projects, found_articles)
