"""
Fetch all project and article data from DvO via its API
"""

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

from django.conf import settings

from construction_work.etl.queries import (
    news_articles,
    projects_with_details,
    work_articles,
)
from core.utils.dvo_utils import DvOClient, DvOResponseError

logger = logging.getLogger(__name__)


def get_all_drupal_projects_with_content() -> dict[str, Any]:
    """
    Return raw construction-work projects and their related raw news articles.

    Projects are fetched first so their news-view paragraph IDs can be used to
    fetch article views concurrently.
    """
    return asyncio.run(_get_all_drupal_projects_with_content())


async def _get_all_drupal_projects_with_content() -> dict[str, Any]:
    async with DvOClient() as client:
        projects = await client.execute_paginated_view_query(
            projects_with_details.QUERY,
            {"paragraphId": settings.DVO_CONSTRUCTION_WORK_PARAGRAPH_ID},
        )

        logger.info(f"Fetched {len(projects)} projects")

        paragraph_ids_by_type = {}
        for project in projects:
            for paragraph_id_dict in extract_news_and_work_paragraph_id_from_project(
                project
            ):
                key = (paragraph_id_dict["paragraph_id"], paragraph_id_dict["type"])
                paragraph_ids_by_type.setdefault(key, paragraph_id_dict)
        paragraph_ids_dicts = list(paragraph_ids_by_type.values())

        news_articles_by_paragraph_id = await client.execute_paginated_view_queries(
            news_articles.QUERY,
            [
                {"paragraphId": paragraph_id_dict["paragraph_id"]}
                for paragraph_id_dict in paragraph_ids_dicts
                if paragraph_id_dict["type"] == "news"
            ],
        )
        logger.info(
            f"Fetched news articles for {len(news_articles_by_paragraph_id)} paragraph IDs"
        )

        work_articles_by_paragraph_id = await client.execute_paginated_view_queries(
            work_articles.QUERY,
            [
                {"paragraphId": paragraph_id_dict["paragraph_id"]}
                for paragraph_id_dict in paragraph_ids_dicts
                if paragraph_id_dict["type"] == "work"
            ],
        )
        logger.info(
            f"Fetched work articles for {len(work_articles_by_paragraph_id)} paragraph IDs"
        )

    return {
        "projects": projects,
        "news_articles": dict(
            zip(
                [
                    paragraph_id_dict["paragraph_id"]
                    for paragraph_id_dict in paragraph_ids_dicts
                    if paragraph_id_dict["type"] == "news"
                ],
                news_articles_by_paragraph_id,
                strict=True,
            )
        ),
        "work_articles": dict(
            zip(
                [
                    paragraph_id_dict["paragraph_id"]
                    for paragraph_id_dict in paragraph_ids_dicts
                    if paragraph_id_dict["type"] == "work"
                ],
                work_articles_by_paragraph_id,
                strict=True,
            )
        ),
    }


def extract_news_and_work_paragraph_id_from_project(
    project: Mapping[str, Any],
) -> list[dict[str, int | str]]:
    """
    Return paragraph IDs for all news and work views in a project.

    Some project payloads include ``None`` placeholders in row content, and older
    news view blocks may omit ``contentIndication`` while still being titled
    ``Nieuws``.

    TODO: once everything is solid in production, this code may be simplified.
    """
    paragraph_ids = []
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
                    and block.get("title") == "Nieuws"
                ):
                    paragraph_id = block.get("id")
                    if isinstance(paragraph_id, int) and not isinstance(
                        paragraph_id, bool
                    ):
                        paragraph_ids.append(
                            {"paragraph_id": paragraph_id, "type": "news"}
                        )
                        continue
                    raise DvOResponseError(
                        "DvO news view paragraph did not contain an integer ID"
                    )

                if (
                    block.get("contentIndication") == "work"
                    and block.get("title") == "Werk aan de weg"
                ):
                    paragraph_id = block.get("id")
                    if isinstance(paragraph_id, int) and not isinstance(
                        paragraph_id, bool
                    ):
                        paragraph_ids.append(
                            {"paragraph_id": paragraph_id, "type": "work"}
                        )
                        continue
                    raise DvOResponseError(
                        "DvO work view paragraph did not contain an integer ID"
                    )
    return paragraph_ids
