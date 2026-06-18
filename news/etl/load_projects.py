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
STALE_PROJECT_DAYS = 5


def projects(project_data):
    if not project_data:
        return

    seen_project_ids = [data.get("id") for data in project_data]
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
            "timeline_title",
            "timeline_intro",
        ],
    )

    project_objects = Project.objects.filter(foreign_id__in=seen_project_ids)
    projects_dict = {project.foreign_id: project for project in project_objects}
    seen_project_primary_keys = [project.id for project in project_objects]
    contacts, timelines, sections, section_urls = (
        [],
        [],
        [],
        [],
    )
    for data in project_data:
        project = projects_dict.get(data.get("id"))
        if project is None:
            continue

        contacts += get_contacts(data, project)
        upsert_images(data, project)

        timelines += get_timeline(data, project)

        new_sections, new_section_urls = get_sections(data, project)
        sections += new_sections
        section_urls += new_section_urls

    with transaction.atomic():
        ProjectContact.objects.filter(project_id__in=seen_project_primary_keys).delete()
        ProjectContact.objects.bulk_create(contacts)

    with transaction.atomic():
        ProjectTimelineItem.objects.filter(
            project_id__in=seen_project_primary_keys
        ).delete()
        parent_ids = {}
        for tl in timelines:
            parent_ids[tl.id] = tl.parent_id
            tl.parent_id = None

        ProjectTimelineItem.objects.bulk_create(timelines)

        for tl in timelines:
            tl.parent_id = parent_ids.get(tl.id)
        ProjectTimelineItem.objects.bulk_update(timelines, ["parent_id"])

    with transaction.atomic():
        ProjectSection.objects.filter(project_id__in=seen_project_primary_keys).delete()
        ProjectSection.objects.bulk_create(sections)
        ProjectSectionUrl.objects.bulk_create(section_urls)

    _deactivate_unseen_projects(seen_project_ids)
    _cleanup_inactive_projects()


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


def _deactivate_unseen_projects(seen_project_ids):
    Project.objects.exclude(foreign_id__in=seen_project_ids).filter(
        hidden=False
    ).update(active=False)


def _cleanup_inactive_projects():
    stale_before = timezone.now() - timezone.timedelta(days=STALE_PROJECT_DAYS)
    Project.objects.filter(
        last_seen__lt=stale_before,
        active=False,
        hidden=False,
    ).delete()


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
    Upsert project images for a given project.

    The project payload can expose its image either through a single `image`
    object or the first entry in an `images` collection. When present, we use
    the largest available source URI for upload and then upsert the persisted
    image variants returned by the ImageSetService.

    The logic is as follows:
    - If an image with the same url already exists for the project, update its width and height
    - If there is an image for a project, but the url is different than the existing one, delete the old image and create a new one
    - If there is no image for a project, create a new one
    """
    image_url = get_project_image_url(project_data)
    if not image_url:
        ProjectImage.objects.filter(parent=project).delete()
        return []

    try:
        image_set_data = IMAGE_SERVICE.get_or_upload_from_url(image_url)
    except (HTTPError, RequestException) as error:
        logger.error(
            "Error getting or uploading image",
            extra={
                "image_url": image_url,
                "project_foreign_id": project_data.get("id"),
            },
            exc_info=error,
        )
        return None

    image_sources = [
        ProjectImage(
            parent=project,
            foreign_id=image_set_data[
                "id"
            ],  # use the image set id as the image foreign_id for reference.
            uri=variant["image"],
            width=variant["width"],
            height=variant["height"],
        )
        for variant in image_set_data.get("variants", [])
    ]
    new_uris = {image.uri for image in image_sources}
    existing_images = ProjectImage.objects.filter(parent=project)
    images_to_delete = existing_images.exclude(uri__in=new_uris)
    if images_to_delete.exists():
        images_to_delete.delete()

    ProjectImage.objects.bulk_create(
        image_sources,
        update_conflicts=True,
        unique_fields=["parent", "uri"],
        update_fields=["foreign_id", "width", "height"],
    )
    return image_sources


def get_project_image_url(project_data: dict) -> str | None:
    image_data = project_data.get("image")
    if not image_data:
        images = project_data.get("images") or []
        image_data = images[0] if images else None

    if not image_data:
        return None

    return get_biggest_source_uri(image_data)


def get_biggest_source_uri(image_data: dict) -> str | None:
    image_sources = image_data.get("sources") or []
    if not image_sources:
        return None

    parsed_sources = []
    for source in image_sources:
        try:
            width = int(source["width"])
            height = int(source["height"])
        except (KeyError, TypeError, ValueError) as error:
            logger.error(
                "Invalid image source width/height data",
                extra={"sources": image_sources, "error": str(error)},
            )
            return None

        uri = source.get("uri")
        if not uri:
            logger.error("Missing image source uri", extra={"sources": image_sources})
            return None

        parsed_sources.append((width * height, uri))

    return max(parsed_sources, key=lambda source: source[0])[1]
