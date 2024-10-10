from django.conf import settings
from django.core.management.base import BaseCommand

from construction_work.etl.update_data import extract_transform_load, garbage_collector
import construction_work.etl.transform_data as transform
import construction_work.etl.load_data as load

from urllib.parse import urljoin

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/construction-work/")
IPROX_PROJECTS_URL = urljoin(IPROX_URL, "projects/")
IPROX_ARTICLES_URL = urljoin(IPROX_URL, "articles/")


class Command(BaseCommand):
    """ Upsert construction work projects and articles """
    help = "Upsert construction work projects and articles"

    def handle(self, *args, **kwargs):
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
        garbage_collector(found_projects, found_articles)
