"""DvO Extract Transform and Load (DvO-ETL)

Fetch data from the DvO API and ingest it into Construction-Work database
"""

from logging import getLogger

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from construction_work.etl.extract_data import get_all_drupal_projects_with_content
from construction_work.etl.load_data import load_data
from construction_work.etl.transform_data import transform_data
from construction_work.models.article_models import Article
from construction_work.models.project_models import Project

logger = getLogger(__name__)


def extract_transform_load():
    """
    Main function call for Fetch and Ingest from DvO to Construction-Work
    """

    ### EXTRACT DATA
    logger.info("Extracting data from DvO")

    extracted_data = get_all_drupal_projects_with_content()
    logger.info("Extracted data from DvO")

    # get project ids from extracted data
    found_project_ids = [project["id"] for project in extracted_data["projects"]]
    found_article_ids = [
        article["id"]
        for articles in extracted_data["news_articles"].values()
        for article in articles
    ]

    logger.info(f"Extracted {len(found_project_ids)} items from DvO")
    logger.info(f"Extracted {len(found_article_ids)} news articles from DvO")

    ### TRANSFORM DATA
    transformed_data = transform_data(extracted_data)
    logger.info(
        f"Transformed {len(transformed_data['projects'])} projects for Construction-Work"
    )

    ### LOAD
    load_data(transformed_data)
    logger.info("Loaded data into Construction-Work")

    return found_project_ids, found_article_ids


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
    unseen_projects = Project.objects.filter(hidden=False).filter(
        Q(drupal_id__isnull=True) | ~Q(drupal_id__in=found_projects)
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
    unseen_articles = Article.objects.filter(
        Q(drupal_id__isnull=True) | ~Q(drupal_id__in=found_articles)
    )
    with transaction.atomic():
        for article in unseen_articles:
            article.deactivate()
