"""
Fetch all project and article data from DvO via its API
"""

import asyncio
from collections.abc import Mapping
from datetime import datetime
from logging import getLogger
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from construction_work.etl.queries import news_articles, projects_with_details
from core.utils.dvo_utils import DvOClient, DvOResponseError

logger = getLogger(__name__)

_REQUIRED_RECORD_FIELDS = (
    "id",
    "title",
    "path",
    "changedDate",
    "publicationDate",
)


def get_all_drupal_projects_with_content() -> dict[str, Any]:
    """
    Return raw construction-work projects and their related raw news articles.

    Projects are fetched first so their news-view paragraph IDs can be used to
    fetch article views concurrently.
    """
    return asyncio.run(_get_all_drupal_projects_with_content())


async def _get_all_drupal_projects_with_content() -> dict[str, Any]:
    async with DvOClient() as client:
        projects = _validate_projects(
            await client.execute_paginated_view_query(
                projects_with_details.QUERY,
                {"paragraphId": settings.DVO_CONSTRUCTION_WORK_PARAGRAPH_ID},
            )
        )

        logger.info(f"Extracted {len(projects)} items from DvO")

        paragraph_ids = list(
            dict.fromkeys(
                paragraph_id
                for project in projects
                if (paragraph_id := extract_news_paragraph_id_from_project(project))
                is not None
            )
        )

        articles_by_paragraph_id = await client.execute_paginated_view_queries(
            news_articles.QUERY,
            [{"paragraphId": paragraph_id} for paragraph_id in paragraph_ids],
        )

        grouped_articles = dict(
            zip(paragraph_ids, articles_by_paragraph_id, strict=True)
        )
        validated_articles = _validate_news_articles(grouped_articles)

    return {"projects": projects, "news_articles": validated_articles}


def _validate_projects(projects: Any) -> list[Mapping[str, Any]]:
    """Validate DvO project records before using them to find news views."""
    if not isinstance(projects, list):
        raise DvOResponseError("DvO projects response must be a list")

    for index, project in enumerate(projects):
        location = f"DvO projects[{index}]"
        if not isinstance(project, Mapping):
            raise DvOResponseError(f"{location} must be an object")
        _validate_record(project, location)

    return projects


def _validate_news_articles(
    news_articles: Any,
) -> Mapping[int | str, list[Mapping[str, Any]]]:
    """Validate the grouped article records returned by DvO news views."""
    if not isinstance(news_articles, Mapping):
        raise DvOResponseError("DvO news articles response must be an object")

    for paragraph_id, articles in news_articles.items():
        if isinstance(paragraph_id, bool) or not isinstance(paragraph_id, (int, str)):
            raise DvOResponseError(
                "DvO news articles keys must be integer or string IDs"
            )
        if isinstance(paragraph_id, str) and not paragraph_id.isdecimal():
            raise DvOResponseError(
                f"DvO news articles key {paragraph_id!r} must contain a numeric ID"
            )
        if not isinstance(articles, list):
            raise DvOResponseError(
                f"DvO news articles[{paragraph_id!r}] must be a list"
            )

        for index, article in enumerate(articles):
            location = f"DvO news articles[{paragraph_id!r}][{index}]"
            if not isinstance(article, Mapping):
                raise DvOResponseError(f"{location} must be an object")
            _validate_record(article, location)

    return news_articles


def _validate_record(record: Mapping[str, Any], location: str) -> None:
    """Validate required fields shared by DvO project and article records."""
    missing_fields = [
        field for field in _REQUIRED_RECORD_FIELDS if record.get(field) is None
    ]
    if missing_fields:
        raise DvOResponseError(
            f"{location} is missing required fields: {', '.join(missing_fields)}"
        )

    record_id = record["id"]
    if isinstance(record_id, bool) or not isinstance(record_id, int):
        raise DvOResponseError(f"{location} field 'id' must be an integer")

    for field in ("title", "path"):
        value = record[field]
        if not isinstance(value, str):
            raise DvOResponseError(f"{location} field {field!r} must be a string")
        if not value.strip():
            raise DvOResponseError(f"{location} field {field!r} must not be empty")

    try:
        URLValidator()(record["path"])
    except ValidationError as error:
        raise DvOResponseError(
            f"{location} field 'path' must be a valid URL"
        ) from error

    for field in ("changedDate", "publicationDate"):
        value = record[field]
        try:
            if isinstance(value, datetime):
                continue
            if not isinstance(value, str):
                raise TypeError
            datetime.fromisoformat(value)
        except (TypeError, ValueError) as error:
            raise DvOResponseError(
                f"{location} field {field!r} must be a valid ISO datetime"
            ) from error


def extract_news_paragraph_id_from_project(
    project: Mapping[str, Any],
) -> int | None:
    """
    Return the first news view paragraph ID, or None if the project has no news view.

    Some project payloads include ``None`` placeholders in row content, and older
    news view blocks may omit ``contentIndication`` while still being titled
    ``Nieuws``.

    TODO: once everything is solid in production, this code may be simplified.
    """
    for grid in project.get("content", []) or []:
        if not isinstance(grid, dict):
            continue
        for row in grid.get("rows", []) or []:
            if not isinstance(row, dict):
                continue
            for block in row.get("content", []) or []:
                if not isinstance(block, dict):
                    continue

                if block.get("__typename") != "ParagraphDdsViews":
                    continue

                if (
                    block.get("contentIndication") == "news"
                    or block.get("title") == "Nieuws"
                ):
                    paragraph_id = block.get("id")
                    if isinstance(paragraph_id, int) and not isinstance(
                        paragraph_id, bool
                    ):
                        return paragraph_id
                    raise DvOResponseError(
                        "DvO news view paragraph did not contain an integer ID"
                    )
    return None
