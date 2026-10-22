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

from construction_work.etl.extract_data import extract_news_paragraph_id_from_project
from core.services.image_set import ImageSetService

logger = logging.getLogger(__name__)


def transform_data(
    extracted_data: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Return loader-ready projects and articles from the extracted DvO response."""
    projects = extracted_data.get("projects", [])
    news_articles = extracted_data.get("news_articles", {})

    transformed_projects = [_transform_project(project) for project in projects]
    transformed_articles = _transform_articles(projects, news_articles)
    return {"projects": transformed_projects, "articles": transformed_articles}


def _transform_project(project: Mapping[str, Any]) -> dict[str, Any]:
    image_set = _transform_image(project["image"]) if project.get("image") else None

    sections: dict[str, list[dict[str, Any]]] = {}
    contacts = []
    timeline_items = []
    timeline_intro = None
    has_timeline = False
    coordinates = None

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
                    contact = _transform_contact(block, body)
                    if contact:
                        contacts.append(contact)

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
        "title": project.get("title"),
        "subtitle": project.get("summaryShort") or project.get("summaryIntroductory"),
        "url": project.get("path"),
        "created": _parse_datetime(project.get("publicationDate")),
        "modified": _parse_datetime(project.get("changedDate")),
        "publicationDate": _parse_datetime(project.get("publicationDate")),
        "expirationDate": None,
        "coordinates": coordinates,
        "sections": sections,
        "contacts": contacts,
        "timeline": {
            "title": "Wanneer" if has_timeline else None,
            "intro": timeline_intro,
            "items": timeline_items,
        },
        "imageSet": image_set,
    }


def _transform_articles(
    projects: list[Mapping[str, Any]],
    articles_by_paragraph_id: Mapping[int | str, list[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    transformed_by_id: dict[Any, dict[str, Any]] = {}

    for project in projects:
        paragraph_id = extract_news_paragraph_id_from_project(project)
        if paragraph_id is None:
            continue

        articles = articles_by_paragraph_id.get(
            paragraph_id, articles_by_paragraph_id.get(str(paragraph_id), [])
        )
        for article in articles:
            article_id = article.get("id")
            transformed = transformed_by_id.get(article_id)
            if transformed is None:
                transformed = _transform_article(article)
                transformed["projectIds"] = []
                transformed_by_id[article_id] = transformed
            project_id = project.get("id")
            if project_id not in transformed["projectIds"]:
                transformed["projectIds"].append(project_id)

    return list(transformed_by_id.values())


def _transform_article(article: Mapping[str, Any]) -> dict[str, Any]:
    image_set = _transform_image(article["image"]) if article.get("image") else None

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
        "type": tags[0].get("name") if tags else None,
        "url": article.get("path"),
        "created": _parse_datetime(article.get("publicationDate")),
        "modified": _parse_datetime(article.get("changedDate")),
        "expirationDate": None,
        "imageSet": image_set,
    }


def _content_blocks(item: Mapping[str, Any]):
    for grid in item.get("content", []) or []:
        if not isinstance(grid, Mapping):
            continue
        for row in grid.get("rows", []) or []:
            if not isinstance(row, Mapping):
                continue
            for block in row.get("content", []) or []:
                if isinstance(block, Mapping):
                    yield block


def _transform_rich_text_block(block: Mapping[str, Any]) -> tuple[str | None, str, str]:
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
    section_names = {
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
    for value in (indication, heading):
        if isinstance(value, str) and (
            section_type := section_names.get(value.strip().lower())
        ):
            return section_type
    return None


_SECTION_TITLES = {
    "what": "Wat",
    "where": "Waar",
    "when": "Wanneer",
    "work": "Werk",
    "contact": "Contact",
}


def _links(body: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(body, "html.parser")
    return [
        {"url": anchor["href"], "label": anchor.get_text(" ", strip=True)}
        for anchor in soup.find_all("a", href=True)
    ]


def _transform_contact(block: Mapping[str, Any], body: str) -> dict[str, Any] | None:
    contact_id = block.get("id")
    if contact_id is None:
        return None

    soup = BeautifulSoup(body, "html.parser")
    name = (soup.find("strong") or soup).get_text(" ", strip=True)
    anchors = soup.find_all("a", href=True)
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
            for line in soup.get_text("\n", strip=True).splitlines()
            if line != name and line not in anchor_texts and line.lower() != "contact"
        ),
        None,
    )

    return {
        "id": contact_id,
        "name": name or None,
        "email": email,
        "phone": phone,
        "position": position,
    }


def _transform_timeline_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title"),
        "body": item.get("description"),
        "collapsed": item.get("initiallyCollapsed"),
        "items": [
            _transform_timeline_item(child) for child in item.get("items", []) or []
        ],
    }


def _transform_coordinates(block: Mapping[str, Any]) -> dict[str, Any] | None:
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
    if value is None:
        return None
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_default_timezone())
    return parsed


def _transform_image(images: list[Mapping[str, Any]]) -> dict[str, Any] | None:
    image_url = images[0].get("src")
    if not isinstance(image_url, str) or not image_url:
        raise ValueError("DvO image did not contain a source path")

    absolute_image_url = urljoin(settings.DVO_URL, image_url)
    try:
        return ImageSetService().get_or_upload_from_url(absolute_image_url)
    except HTTPError as e:
        logger.error(f"Error getting or uploading image: {e}")
        return None
