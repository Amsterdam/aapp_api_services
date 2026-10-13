"""DvO Extract Transform and Load (DvO-ETL)

Fetch data from the DvO API and ingest it into Construction-Work database
"""

from logging import getLogger

from django.db import transaction
from django.utils import timezone

from construction_work.etl.extract_data import get_all_drupal_projects_with_content
from construction_work.models.article_models import Article
from construction_work.models.project_models import Project

logger = getLogger(__name__)


def extract_transform_load(*, transform_func, load_func):
    """
    Main function call for Fetch and Ingest from DvO to Construction-Work
    """
    ### EXTRACT DATA
    logger.info("Extracting data from DvO")

    extracted_data = get_all_drupal_projects_with_content()
    logger.info("Extracted data from DvO")
    logger.info(f"Extracted {len(extracted_data['nodes'])} items from DvO")
    all_iprox_items = extracted_data["nodes"]
    logger.info(f"First extracted items: {all_iprox_items[:2]}")

    ### TRANSFORM DATA
    logger.info("Transforming data for Construction-Work")
    transformed_data = transform_func(extracted_data)

    ### LOAD DATA
    logger.info("Ingesting data into Construction-Work")
    load_func(transformed_data)

    logger.info("Data ingestion finished!")
    return [item["id"] for item in all_iprox_items]


def garbage_collector(found_projects, found_articles):
    initial_projects_count = Project.objects.all().count()

    _deactivate_unseen_projects(found_projects)
    _cleanup_inactive_projects()
    _deactivate_unseen_articles(found_articles)

    garbage_collector_status = {
        "projects": {
            "active": Project.objects.filter(active=True).count(),
            "inactive": Project.objects.filter(active=False).count(),
            "deleted": initial_projects_count - Project.objects.all().count(),
            "count": Project.objects.all().count(),
        },
        "articles": {
            "active": Article.objects.filter(active=True).count(),
            "inactive": Article.objects.filter(active=False).count(),
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


def _deactivate_unseen_articles(found_articles):
    unseen_articles = Article.objects.exclude(foreign_id__in=found_articles)
    with transaction.atomic():
        for article in unseen_articles:
            article.deactivate()
