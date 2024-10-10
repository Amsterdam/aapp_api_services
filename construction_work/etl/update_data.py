""" IPROX Extract Transform and Load (IPROX-ETL)

    Fetch data from the IPROX API and ingest it into Construction-Work database
"""

from logging import getLogger

from django.db import transaction
from django.utils import timezone

from construction_work.etl.extract_data import get_all_iprox_items, get_iprox_items_data
from construction_work.models import Article, Project

logger = getLogger(__name__)


def extract_transform_load(*, iprox_url, transform_func, load_func):
    """
    Main function call for Fetch and Ingest from Iprox to Construction-Work
    """
    ### EXTRACT DATA
    logger.info("Extracting data from IPROX")

    # Collect all items in iprox
    all_iprox_items = get_all_iprox_items(iprox_url)
    extracted_data = get_iprox_items_data(
        url=iprox_url, item_ids=[item["id"] for item in all_iprox_items]
    )

    ### TRANSFORM DATA
    logger.info("Transforming data for Construction-Work")
    transformed_data = transform_func(extracted_data)

    ### LOAD DATA
    logger.info("Ingesting data into Construction-Work")
    load_func(transformed_data)

    return [item["id"] for item in all_iprox_items]


def garbage_collector(found_projects, found_articles):
    initial_projects_count = Project.objects.all().count()

    _deactivate_unseen_projects(found_projects)
    _cleanup_inactive_projects()
    initial_article_count = _remove_unseen_articles(found_articles)

    garbage_collector_status = {
        "projects": {
            "active": Project.objects.filter(active=True).count(),
            "inactive": Project.objects.filter(active=False).count(),
            "deleted": initial_projects_count - Project.objects.all().count(),
            "count": Project.objects.all().count(),
        },
        "articles": {
            "deleted": initial_article_count - Article.objects.all().count(),
            "count": Article.objects.all().count(),
        },
    }
    logger.info(garbage_collector_status)


def _deactivate_unseen_projects(found_projects):
    unseen_projects = Project.objects.exclude(foreign_id__in=found_projects).filter(
        hidden=False
    )
    with transaction.atomic():
        for project in unseen_projects:
            project.deactivate()


def _cleanup_inactive_projects():
    five_days_ago = timezone.now() - timezone.timedelta(days=5)
    Project.objects.filter(
        last_seen__lt=five_days_ago, active=False, hidden=False
    ).delete()


def _remove_unseen_articles(found_articles):
    initial_article_count = Article.objects.all().count()
    Article.objects.exclude(foreign_id__in=found_articles).delete()
    return initial_article_count
