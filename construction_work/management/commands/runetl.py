from django.core.management.base import BaseCommand

from construction_work.etl.update_data import extract_transform_load


class Command(BaseCommand):
    """Upsert construction work projects and articles"""

    help = "Upsert construction work projects and articles"

    def handle(self, *args, **kwargs):
        # current_article_ids = set(Article.objects.values_list("foreign_id", flat=True))
        _ = extract_transform_load()

        # send_article_notifications(current_article_ids, found_articles)
        # garbage_collector(found_projects, found_articles)
