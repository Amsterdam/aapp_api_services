"""Write all project and article data from IPROX to Construction Work database
See README.md for more info regarding the IPROX API
"""

from logging import getLogger

from django.db import transaction
from django.utils import timezone
from requests import HTTPError

from construction_work.models.article_models import (
    Article,
    ArticleImage,
    ArticleImageSource,
)
from construction_work.models.project_models import (
    Project,
    ProjectContact,
    ProjectImage,
    ProjectImageSource,
    ProjectSection,
    ProjectSectionUrl,
    ProjectTimelineItem,
)
from core.services.image_set import ImageSetService

logger = getLogger(__name__)


def projects(project_data):
    projects_list = [get_project_object(data) for data in project_data]
    Project.objects.bulk_create(
        projects_list,
        update_conflicts=True,
        unique_fields=["foreign_id"],
        update_fields=[
            "title",
            "subtitle",
            "url",
            "coordinates_lat",
            "coordinates_lon",
            "creation_date",
            "modification_date",
            "publication_date",
            "expiration_date",
            "last_seen",
            "active",
        ],
    )

    project_objects = Project.objects.all()
    projects_dict = {project.foreign_id: project for project in project_objects}
    contacts, images, image_sources, timelines, sections, section_urls = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for data in project_data:
        project = projects_dict.get(data.get("id"))

        contacts += get_contacts(data, project)

        new_images, new_image_sources = store_image(
            data,
            project,
            image_class=ProjectImage,
            image_source_class=ProjectImageSource,
        )

        images += new_images
        image_sources += new_image_sources

        timelines += get_timeline(data, project)

        new_sections, new_section_urls = get_sections(data, project)
        sections += new_sections
        section_urls += new_section_urls

    with transaction.atomic():
        ProjectContact.objects.all().delete()
        ProjectContact.objects.bulk_create(contacts)

    with transaction.atomic():
        ProjectImage.objects.all().delete()
        ProjectImage.objects.bulk_create(images)
        ProjectImageSource.objects.bulk_create(image_sources)

    with transaction.atomic():
        ProjectTimelineItem.objects.all().delete()
        parent_ids = {}
        for tl in timelines:
            parent_ids[tl.id] = tl.parent_id
            tl.parent_id = None

        ProjectTimelineItem.objects.bulk_create(timelines)

        for tl in timelines:
            tl.parent_id = parent_ids.get(tl.id)
        ProjectTimelineItem.objects.bulk_update(timelines, ["parent_id"])

    with transaction.atomic():
        ProjectSection.objects.all().delete()
        ProjectSection.objects.bulk_create(sections)
        ProjectSectionUrl.objects.bulk_create(section_urls)


def get_project_object(data):
    timeline_data = data.get("timeline") or {}
    coordinates_data = data.get("coordinates") or {}
    sections_filled = check_sections_filled(data)
    project = Project(
        foreign_id=data.get("id"),
        title=data.get("title"),
        subtitle=data.get("subtitle"),
        timeline_title=timeline_data.get("title"),
        timeline_intro=timeline_data.get("intro"),
        coordinates_lat=coordinates_data.get("lat"),
        coordinates_lon=coordinates_data.get("lon"),
        url=data.get("url"),
        creation_date=data.get("created"),
        modification_date=data.get("modified"),
        # 133548: the publicationDate field is filled with the modification date from Iprox' side,
        # because of that we will use the created date as publication date
        publication_date=data.get("created"),
        expiration_date=data.get("expirationDate"),
        last_seen=timezone.now(),
        # only projects with filled sections are set to active, because those are
        # the only ones that can be shown on the frontend in a proper way.
        active=sections_filled,
    )
    return project


def check_sections_filled(data):
    sections_data = data.get("sections") or {}
    for _, value in sections_data.items():
        if value:
            return True
    return False


def get_contacts(data, project):
    if not data.get("contacts"):
        return []
    return [ProjectContact(project=project, **c) for c in data.get("contacts")]


def get_timeline(data, project):
    timeline_data = data.get("timeline") or {}
    if not timeline_data.get("items"):
        return []
    items = []
    for item in timeline_data.get("items"):
        items += get_timeline_items(item, project=project)
    return items


def get_timeline_items(timeline_data, project=None, parent=None):
    parent = ProjectTimelineItem(
        title=timeline_data.get("title"),
        body=timeline_data.get("body"),
        collapsed=timeline_data.get("collapsed"),
        project=project,
        parent=parent,
    )
    timeline_items = [parent]
    if timeline_data.get("items"):
        for item in timeline_data.get("items"):
            timeline_items += get_timeline_items(item, parent=parent)
    return timeline_items


def get_sections(data, project):
    sections, section_urls = [], []
    if not data.get("sections"):
        return sections, section_urls
    for section_type, value in data.get("sections").items():
        for item in value:
            section = ProjectSection(
                project=project,
                body=item.get("body"),
                type=section_type,
            )
            if title := item.get("title"):
                section.title = title
            sections.append(section)
            section_urls += [
                ProjectSectionUrl(section=section, **v) for v in item.get("links")
            ]
    return sections, section_urls


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
                logger.error(
                    f"Project ID {id} not found in database",
                    extra={
                        "project_id": id,
                        "article_id": item.get("id"),
                    },
                )
        article_project_mapping[article_object.foreign_id] = projects

    Article.objects.bulk_create(
        articles,
        update_conflicts=True,
        unique_fields=["foreign_id"],
        update_fields=[
            "title",
            "intro",
            "body",
            "type",
            "url",
            "creation_date",
            "modification_date",
            "publication_date",
            "expiration_date",
        ],
    )

    # Projects can only be set after the articles are saved, because they are a many-to-many relationship
    articles_saved = Article.objects.filter(
        foreign_id__in=[article for article in article_project_mapping.keys()]
    )
    with transaction.atomic():
        for article in articles_saved:
            projects = article_project_mapping.get(article.foreign_id)
            article.projects.set(projects)

    articles_dict = {article.foreign_id: article for article in articles_saved}
    images, image_sources = [], []
    for data in article_data:
        article = articles_dict.get(data.get("id"))
        new_images, new_image_sources = store_image(
            data,
            article,
            image_class=ArticleImage,
            image_source_class=ArticleImageSource,
        )
        images += new_images
        image_sources += new_image_sources

    with transaction.atomic():
        ArticleImage.objects.all().delete()
        ArticleImage.objects.bulk_create(images)
        ArticleImageSource.objects.bulk_create(image_sources)


def get_article_object(data):
    article = Article(
        foreign_id=data.get("id"),
        title=data.get("title"),
        intro=data.get("intro"),
        body=data.get("body"),
        type=data.get("type"),
        url=data.get("url"),
        creation_date=data.get("created"),
        modification_date=data.get("modified"),
        # 133548: the publicationDate field is filled with the modification date from Iprox' side,
        # because of that we will use the created date as publication date
        publication_date=data.get("created"),
        expiration_date=data.get("expirationDate"),
    )
    return article


def store_image(
    project_data, parent, image_class, image_source_class
) -> tuple[list, list]:
    image_data = project_data.get("image")
    if not image_data and project_data.get("images"):
        image_data = project_data.get("images")[0]
    if not image_data:
        return [], []
    image = image_class(
        id=image_data.get("id"),
        aspectRatio=image_data.get("aspectRatio"),
        alternativeText=image_data.get("alternativeText"),
        parent=parent,
    )

    image_data_sources = image_data.get("sources")
    if not image_data_sources:
        return [], []

    for source in image_data_sources:
        try:
            source["width"] = int(source["width"])
            source["height"] = int(source["height"])
        except (KeyError, ValueError) as e:
            logger.error(
                "Invalid image source width/height data",
                extra={"sources": image_data_sources, "error": e},
            )
            return [], []

    biggest_source_image = max(
        image_data_sources,
        key=lambda s: s["width"] * s["height"],
    )
    if not biggest_source_image.get("uri"):
        logger.error("Missing image source uri", extra={"sources": image_data_sources})
        return [], []

    try:
        image_set_data = ImageSetService().get_or_upload_from_url(
            biggest_source_image["uri"]
        )
    except HTTPError as e:
        logger.error(f"Error getting or uploading image: {e}")
        return [], []

    image.image_set = image_set_data["id"]

    image_sources = [
        image_source_class(
            image=image,
            uri=v["image"],
            width=v["width"],
            height=v["height"],
        )
        for v in image_set_data["variants"]
    ]
    return [image], image_sources
