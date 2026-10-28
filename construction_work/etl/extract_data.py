"""
Fetch all project and article data from DvO via its API
"""

import asyncio
from collections.abc import Mapping
from typing import Any

from django.conf import settings

from construction_work.etl.queries import (
    news_articles,
    projects_with_details,
    work_articles,
)
from core.utils.dvo_utils import DvOClient, DvOResponseError


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

        paragraph_ids_dicts = list(
            dict.fromkeys(
                paragraph_id
                for project in projects
                if (
                    paragraph_id := extract_news_and_work_paragraph_id_from_project(
                        project
                    )
                )
                is not None
            )
        )

        news_articles_by_paragraph_id = await client.execute_paginated_view_queries(
            news_articles.QUERY,
            [
                {"paragraphId": paragraph_id_dict["paragraph_id"]}
                for paragraph_id_dict in paragraph_ids_dicts
                if paragraph_id_dict["type"] == "news"
            ],
        )

        work_articles_by_paragraph_id = await client.execute_paginated_view_queries(
            work_articles.QUERY,
            [
                {"paragraphId": paragraph_id_dict["paragraph_id"]}
                for paragraph_id_dict in paragraph_ids_dicts
                if paragraph_id_dict["type"] == "work"
            ],
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
                    and block.get("title") == "Nieuws"
                ):
                    paragraph_id = block.get("id")
                    if isinstance(paragraph_id, int) and not isinstance(
                        paragraph_id, bool
                    ):
                        return {"paragraph_id": paragraph_id, "type": "news"}
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
                        return {"paragraph_id": paragraph_id, "type": "work"}
                    raise DvOResponseError(
                        "DvO work view paragraph did not contain an integer ID"
                    )
    return None
