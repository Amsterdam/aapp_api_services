from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

import construction_work.etl.load_data as load
import construction_work.etl.transform_data as transform
from construction_work.etl.send_notifications import send_article_notifications
from construction_work.etl.update_data import extract_transform_load, garbage_collector
from construction_work.models.article_models import Article

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/construction-work/")
IPROX_PROJECTS_URL = urljoin(IPROX_URL, "projects/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "articles/")


class Command(BaseCommand):
    """Upsert construction work projects and articles"""

    help = "Upsert construction work projects and articles"

    def handle(self, *args, **kwargs):
        current_article_ids = set(Article.objects.values_list("foreign_id", flat=True))
        found_projects = extract_transform_load(
            iprox_url=IPROX_PROJECTS_URL,
            transform_func=transform.projects,
            load_func=load.projects,
        )
        found_articles = extract_transform_load(
            iprox_url=IPROX_ARTICLES_URL,
            transform_func=transform.articles,
            load_func=load.articles,
        )
        send_article_notifications(current_article_ids, found_articles)
        garbage_collector(found_projects, found_articles)
