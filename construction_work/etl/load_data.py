""" Write all project and article data from IPROX to Construction Work database
    See README.md for more info regarding the IPROX API
"""
from django.db import transaction
from django.utils import timezone
from construction_work.models import Project, Article

from logging import getLogger
logger = getLogger(__name__)


def projects(project_data):
    projects = []
    for item in project_data:
        project_object = get_project_object(item)
        projects.append(project_object)

    Project.objects.bulk_create(
        projects,
        update_conflicts=True,
        unique_fields=["foreign_id"],
        update_fields=[
            "title",
            "subtitle",
            "sections",
            "contacts",
            "timeline",
            "image",
            "images",
            "url",
            "coordinates",
            "creation_date",
            "modification_date",
            "publication_date",
            "expiration_date",
            "last_seen",
            "active",
        ]
    )

def get_project_object(data):
    project = Project(
        title=data.get("title", ""),
        subtitle=data.get("subtitle", ""),
        sections = data.get("sections"),
        contacts = data.get("contacts"),
        timeline = data.get("timeline"),
        image = data.get("image"),
        images = data.get("images"),
        url = data.get("url"),
        foreign_id = data.get("id"),
        coordinates = data.get("coordinates"),
        creation_date = data.get("created"),
        modification_date = data.get("modified"),
        publication_date = data.get("publicationDate"),
        expiration_date = data.get("expirationDate"),
        last_seen=timezone.now(),
        active = True,
    )
    return project


def articles(article_data):
    articles, article_project_mapping = [], {}
    project_dict = {project.foreign_id: project for project in Project.objects.all()}
    for item in article_data:
        foreign_project_ids = list(item.pop("projectIds"))
        article_object = get_article_object(item)
        articles.append(article_object)

        projects = []
        for id in foreign_project_ids:
            proj = project_dict.get(id)
            if proj:
                projects.append(proj)
            else:
                logger.error(f"Project ID {id} not found in database",
                               extra={"project_id": id, "article_id": item.get("id")})
        article_project_mapping[article_object.foreign_id] = projects

    Article.objects.bulk_create(
        articles,
        update_conflicts=True,
        unique_fields=["foreign_id"],
        update_fields=[
            "title",
            "intro",
            "body",
            "image",
            "type",
            "url",
            "creation_date",
            "modification_date",
            "publication_date",
            "expiration_date",
        ]
    )

    # Projects can only be set after the articles are saved, because they are a many-to-many relationship
    articles_saved = Article.objects.filter(foreign_id__in=[article for article in article_project_mapping.keys()])
    with transaction.atomic():
        for article in articles_saved:
            projects = article_project_mapping.get(article.foreign_id)
            article.projects.set(projects)

def get_article_object(data):
    article = Article(
        foreign_id=data.get("id"),
        title=data.get("title"),
        intro=data.get("intro"),
        body=data.get("body"),
        image=data.get("image"),
        type=data.get("type"),
        url=data.get("url"),
        creation_date=data.get("created"),
        modification_date=data.get("modified"),
        publication_date=data.get("publicationDate"),
        expiration_date=data.get("expirationDate"),
    )
    return article