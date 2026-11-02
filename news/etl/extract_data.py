"""Extract news articles and blogs from DvO."""

import asyncio
from typing import Any

from django.conf import settings

from core.utils.dvo_utils import DvOClient
from news.etl.queries import news_blogs_ids, news_blogs_with_content


def get_all_drupal_news() -> dict[str, list[dict[str, Any]]]:
    """Return all raw news and blog nodes from the DvO news view."""
    return asyncio.run(_get_all_drupal_news())


async def _get_all_drupal_news() -> dict[str, list[dict[str, Any]]]:
    async with DvOClient() as client:
        all_news = await client.execute_paginated_view_query(
            news_blogs_with_content.QUERY,
            {"paragraphId": settings.DVO_NEWS_PARAGRAPH_ID},
        )

        highlighted_news = await client.execute_paginated_view_query(
            news_blogs_ids.QUERY,
            {"paragraphId": settings.DVO_NEWS_HIGHLIGHTED_PARAGRAPH_ID, "page": 1},
        )

        result = {
            "all_news": all_news,
            "highlighted_news": highlighted_news,
        }

        return result
