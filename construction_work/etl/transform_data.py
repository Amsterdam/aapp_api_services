"""Transform extracted DvO data into the structures expected by the loader."""

import logging
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from requests import HTTPError

from construction_work.etl.extract_data import (
    extract_news_and_work_paragraph_id_from_project,
)
from core.services.image_set import ImageSetService

logger = logging.getLogger(__name__)

_SECTION_MAPPING = {
    "what": "what",
    "wat": "what",
    "where": "where",
    "waar": "where",
    "when": "when",
    "wanneer": "when",
    "work": "work",
    "werk": "work",
    "werkzaamheden": "work",
    "contact": "contact",
}


_SECTION_TITLES = {
    "what": "Wat",
    "where": "Waar",
    "when": "Wanneer",
    "work": "Werk",
    "contact": "Contact",
}


def transform_data(
    extracted_data: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Return loader-ready projects and articles from the extracted DvO response."""
    projects = extracted_data["projects"]
    news_articles = extracted_data["news_articles"]
    work_articles = extracted_data["work_articles"]
    image_set_service = ImageSetService()

    transformed_projects = [
        _transform_project(project, image_set_service) for project in projects
    ]
    transformed_articles = _transform_articles(
        projects, news_articles, image_set_service, "news"
    )
    transformed_articles += _transform_articles(
        projects, work_articles, image_set_service, "work"
    )
    return {"projects": transformed_projects, "articles": transformed_articles}


def _transform_project(
    project: Mapping[str, Any],
    image_set_service: ImageSetService | None,
) -> dict[str, Any]:
    """Convert a DvO project, including its content blocks, to loader fields."""
    image_set = None
    if project.get("image"):
        if image_set_service is None:
            raise RuntimeError("ImageSetService is required for project images")
        image_set = _transform_image(project["image"], image_set_service)

    sections = {}
    contacts = []
    timeline_items = []
    timeline_intro = None
    has_timeline = False
    coordinates = None

    raw_title = project.get("title", "")
    project_title = raw_title.split(":")[0]
    project_subtitle = _get_subtitle(raw_title)

    for block in _content_blocks(project):
        typename = block.get("__typename")

        if typename == "ParagraphDdsRichText":
            section_type, title, body = _transform_rich_text_block(block)
            if section_type:
                section = {
                    "body": body,
                    "links": _links(body),
                    "title": title,
                }
                sections.setdefault(section_type, []).append(section)
                if section_type == "contact":
                    contacts.extend(_transform_contacts(body))

        elif typename == "ParagraphDdsProgressList":
            has_timeline = True
            timeline_items.extend(
                _transform_timeline_item(item) for item in block.get("items", [])
            )
            timeline_intro = block.get("intro") or timeline_intro

        elif (
            "mapDataset" in block or typename == "ParagraphDdsMapDataset"
        ) and coordinates is None:
            coordinates = _transform_coordinates(block)

    return {
        "id": project.get("id"),
        "title": project_title,
        "subtitle": project_subtitle,
        "url": project.get("path"),
        # there is no creation date field in the source data, so it is filled with the publication date
        "creation_date": _parse_datetime(project.get("publicationDate")),
        "modification_date": _parse_datetime(project.get("changedDate")),
        "publication_date": _parse_datetime(project.get("publicationDate")),
        # there is no expiration date field in the source data, so it is set to None
        "expiration_date": None,
        "coordinates_lat": coordinates["lat"] if coordinates else None,
        "coordinates_lon": coordinates["lon"] if coordinates else None,
        "sections": sections,
        "contacts": contacts,
        "timeline": {
            "title": "Wanneer" if has_timeline else None,
            "intro": timeline_intro,
            "items": timeline_items,
        },
        "image_set": image_set,
    }


def _transform_articles(
    projects: list[Mapping[str, Any]],
    articles_by_paragraph_id: Mapping[int | str, list[Mapping[str, Any]]],
    image_set_service: ImageSetService | None,
    article_type: str,
) -> list[dict[str, Any]]:
    """Transform news articles and associate each with its related projects."""
    transformed_by_id = {}

    for project in projects:
        for paragraph_id_dict in extract_news_and_work_paragraph_id_from_project(
            project
        ):
            if paragraph_id_dict["type"] != article_type:
                continue
            paragraph_id = paragraph_id_dict["paragraph_id"]

            articles = articles_by_paragraph_id.get(
                paragraph_id, articles_by_paragraph_id.get(str(paragraph_id), [])
            )
            for article in articles:
                article_id = article.get("id")
                transformed = transformed_by_id.get(article_id)
                if transformed is None:
                    transformed = _transform_article(
                        article, image_set_service, article_type
                    )
                    transformed["projectIds"] = []
                    transformed_by_id[article_id] = transformed
                project_id = project.get("id")
                if project_id not in transformed["projectIds"]:
                    transformed["projectIds"].append(project_id)

    return list(transformed_by_id.values())


def _transform_article(
    article: Mapping[str, Any],
    image_set_service: ImageSetService | None,
    article_type: str,
) -> dict[str, Any]:
    """Convert a DvO news article and its content to loader fields."""
    image_set = None
    if article.get("image"):
        if image_set_service is None:
            raise RuntimeError("ImageSetService is required for article images")
        image_set = _transform_image(article["image"], image_set_service)

    body = "".join(
        block.get("content") or ""
        for block in _content_blocks(article)
        if isinstance(block.get("content"), str)
    )
    tags = article.get("tag") or []
    if isinstance(tags, Mapping):
        tags = [tags]

    return {
        "id": article.get("id"),
        "title": article.get("title"),
        "intro": article.get("summaryShort"),
        "body": body,
        "type": article_type,
        "url": article.get("path"),
        "creation_date": _parse_datetime(article.get("publicationDate")),
        "publication_date": _parse_datetime(article.get("publicationDate")),
        "modification_date": _parse_datetime(article.get("changedDate")),
        "expiration_date": None,
        "image_set": image_set,
    }


def _content_blocks(item: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return mapping-valued content blocks from an item's grid rows."""
    blocks = []
    for grid in item.get("content", []) or []:
        if not isinstance(grid, Mapping):
            continue
        for row in grid.get("rows", []) or []:
            if not isinstance(row, Mapping):
                continue
            for block in row.get("content", []) or []:
                if isinstance(block, Mapping):
                    blocks.append(block)
    return blocks


def _transform_rich_text_block(block: Mapping[str, Any]) -> tuple[str | None, str, str]:
    """Extract a section type, heading, and body HTML from rich-text content."""
    content = block.get("content") or ""
    soup = BeautifulSoup(content, "html.parser")
    heading = soup.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    heading_text = heading.get_text(" ", strip=True) if heading else ""

    section_type = _section_type(block.get("contentIndication"), heading_text)
    if heading:
        heading.decompose()
    body = "".join(str(element) for element in soup.contents).strip()
    section_title = heading_text or _SECTION_TITLES.get(section_type, "")
    return section_type, section_title, body


def _section_type(indication: Any, heading: str) -> str | None:
    """Map a DvO section indication or heading to a loader section type."""
    for value in (indication, heading):
        if isinstance(value, str) and (
            section_type := _SECTION_MAPPING.get(value.strip().lower())
        ):
            return section_type
    return None


def _links(body: str) -> list[dict[str, str]]:
    """Extract link URLs and labels from a section's HTML body."""
    soup = BeautifulSoup(body, "html.parser")
    return [
        {"url": anchor["href"], "label": anchor.get_text(" ", strip=True)}
        for anchor in soup.find_all("a", href=True)
    ]


def _transform_contacts(body: str) -> list[dict[str, Any]]:
    """Extract each contact paragraph from rich-text HTML."""
    soup = BeautifulSoup(body, "html.parser")
    contact_paragraphs = soup.find_all("p") or [soup]
    contacts = []

    for paragraph in contact_paragraphs:
        name = (paragraph.find("strong") or paragraph).get_text(" ", strip=True)
        anchors = paragraph.find_all("a", href=True)
        email = next(
            (
                anchor["href"].removeprefix("mailto:")
                for anchor in anchors
                if anchor["href"].startswith("mailto:")
            ),
            None,
        )
        phone = next(
            (
                anchor["href"].removeprefix("tel:")
                for anchor in anchors
                if anchor["href"].startswith("tel:")
            ),
            None,
        )
        anchor_texts = {anchor.get_text(" ", strip=True) for anchor in anchors}
        position = next(
            (
                line
                for line in paragraph.get_text("\n", strip=True).splitlines()
                if line != name
                and line not in anchor_texts
                and line.lower() != "contact"
            ),
            None,
        )
        extra = next(
            (
                line
                for line in paragraph.get_text("\n", strip=True).splitlines()
                if line != name
                and line not in anchor_texts
                and line.lower() != "contact"
                and line != position
            ),
            None,
        )
        contacts.append(
            {
                "name": name or None,
                "email": email,
                "phone": phone,
                "position": position,
                "extra": extra,
            }
        )

    return contacts


def _transform_timeline_item(item: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a progress-list item and its nested items to loader fields."""
    return {
        "title": item.get("title"),
        "body": item.get("description"),
        "collapsed": item.get("initiallyCollapsed"),
        "items": [
            _transform_timeline_item(child) for child in item.get("items", []) or []
        ],
    }


def _transform_coordinates(block: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the first point's latitude and longitude from a map block."""
    for dataset in block.get("mapDataset", []) or []:
        for point in dataset.get("pointsOfInterest", []) or []:
            location = point.get("location")
            if location:
                return {
                    "lat": location.get("latitude"),
                    "lon": location.get("longitude"),
                }
    return None


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse a DvO datetime and make naive values timezone-aware."""
    if value is None:
        return None
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_default_timezone())
    return parsed


def _transform_image(
    images: list[Mapping[str, Any]],
    image_set_service: ImageSetService,
) -> dict[str, Any] | None:
    """Upload the first DvO image by URL and return its image-set data."""
    image_url = images[0].get("src")
    if not isinstance(image_url, str) or not image_url:
        raise ValueError("DvO image did not contain a source path")

    absolute_image_url = urljoin(settings.DVO_URL, image_url)
    try:
        image_set = image_set_service.get_or_upload_from_url(absolute_image_url)
    except HTTPError as e:
        logger.error(f"Error getting or uploading image: {e}")
        return None
    source_image = images[0]
    return {
        **image_set,
        **({"image_id": source_image["id"]} if "id" in source_image else {}),
        **{
            key: source_image[key]
            for key in ("aspectRatio", "alternativeText")
            if key in source_image
        },
    }


def _get_subtitle(title: str) -> str | None:
    """Extract the subtitle from a title string if present."""
    if not title:
        return None
    parts = title.split(":", 1)
    subtitle = parts[1] if len(parts) > 1 else None
    # delete leading space if present and capitalize
    subtitle = subtitle.lstrip().capitalize() if subtitle else None
    return subtitle
