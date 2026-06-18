"""Write all project and article data from IPROX to Construction Work database
See README.md for more info regarding the IPROX API
"""

from logging import getLogger

from django.db import transaction
from django.utils import timezone
from requests import HTTPError, RequestException

from core.services.image_set import ImageSetService
from news.models.project_models import (
    Project,
    ProjectContact,
    ProjectImage,
    ProjectSection,
    ProjectSectionUrl,
    ProjectTimelineItem,
)

logger = getLogger(__name__)
IMAGE_SERVICE = ImageSetService()


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
    contacts, timelines, sections, section_urls = (
        [],
        [],
        [],
        [],
    )
    for data in project_data:
        project = projects_dict.get(data.get("id"))

        contacts += get_contacts(data, project)
        upsert_images(data, project)

        timelines += get_timeline(data, project)

        new_sections, new_section_urls = get_sections(data, project)
        sections += new_sections
        section_urls += new_section_urls

    with transaction.atomic():
        ProjectContact.objects.all().delete()
        ProjectContact.objects.bulk_create(contacts)

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
    for value in sections_data.values():
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


def upsert_images(project_data: dict, project: Project):
    """
    Upsert article images for a given article. If the article has an image_url, we will attempt to get or upload the image using the ImageSetService.
    Then we will upsert the NewsArticleImage instances for the article based on the image variants returned by the ImageSetService.
    The logic is as follows:
    - If an image with the same url already exists for the article, update its width and height
    - If there is an image for an article, but the url is different than the existing one, delete the old image and create a new one
    - If there is no image for an article, create a new one
    """
    image_url = project_data.get("image_url")
    if image_url:
        try:
            image_set_data = IMAGE_SERVICE.get_or_upload_from_url(image_url)
        except (HTTPError, RequestException) as e:
            logger.error(
                "Error getting or uploading image",
                extra={"image_url": image_url, "error": str(e)},
            )
            return

        # upsert article images
        image_sources = [
            ProjectImage(
                parent=project,
                foreign_id=image_set_data[
                    "id"
                ],  # use the image set id as the image foreign_id for reference.
                uri=v["image"],
                width=v["width"],
                height=v["height"],
            )
            for v in image_set_data["variants"]
        ]
        # Gather all URIs for this article from the new image_sources
        new_uris = {img.uri for img in image_sources}
        # Find all existing images for this article
        existing_images = ProjectImage.objects.filter(parent=project)
        # Delete images for this article whose URI is not in the new set
        images_to_delete = existing_images.exclude(uri__in=new_uris)
        if images_to_delete.exists():
            images_to_delete.delete()

        # Upsert new images (create or update width/height)
        ProjectImage.objects.bulk_create(
            image_sources,
            update_conflicts=True,
            unique_fields=["parent", "uri"],
            update_fields=["width", "height"],
        )
        return image_sources
