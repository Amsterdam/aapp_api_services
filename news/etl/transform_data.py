import html
import logging
import re
from urllib.parse import urljoin

from django.conf import settings

from news.enums.news_article import NewsArticleSource

logger = logging.getLogger(__name__)

TAG_MAPPING = NewsArticleSource.choices_as_dict()
REQUIRED_DRUPAL_FIELDS = ("id", "title", "changedDate", "publicationDate", "path")


def transform(extracted_data: dict[str, list[dict]]) -> list[dict]:
    """
    Transform the extracted news articles data into a list of transformed articles (dicts).
    - Cleans 'body' and text fields
    - Deduplicates by id
    - Logs and skips invalid articles
    """

    transformed = []
    for article in extracted_data:
        missing_fields = [
            field for field in REQUIRED_DRUPAL_FIELDS if not article.get(field)
        ]

        if missing_fields:
            logger.warning(
                "Skipping Drupal node with missing required fields",
                extra={
                    "article_id": article.get("id"),
                    "missing_fields": missing_fields,
                },
            )
            continue

        article_properties = get_article_properties(
            article.get("tag", []), article.get("__typename")
        )
        article_image = article.get("image", [])[0] if article.get("image") else None

        # Clean and transform fields
        transformed.append(
            {
                "foreign_id": article.get("id"),
                "type": article.get("__typename"),
                "title": article.get("title"),
                "article_body": get_body_from_content(
                    article.get("content", []), article.get("id")
                ),
                "liveblog_messages": get_liveblog_messages(
                    article.get("blogEntries", [])
                ),
                "summary": article.get("summaryShort"),
                "intro": article.get("summaryIntroductory"),
                "in_all_news": article_properties.get("in_all_news", False),
                "is_highlight": article_properties.get("is_highlight", False),
                "is_liveblog": article_properties.get("is_liveblog", False),
                "is_district": article_properties.get("is_district", False),
                "district": article_properties.get("district"),
                "url": article.get("path"),
                "creation_datetime": article.get("publicationDate"),
                "modification_datetime": article.get("changedDate"),
                "publication_datetime": article.get("publicationDate"),
                "expiration_datetime": article.get("expirationDate"),
                "image": {
                    "url": construct_image_url(article_image.get("src"))
                    if article_image
                    else None,
                    "alt": article_image.get("alt") if article_image else None,
                    "description": article_image.get("description")
                    if article_image
                    else None,
                },
                "is_active_liveblog": article_properties.get(
                    "is_active_liveblog", False
                ),
            }
        )
    return transformed


def get_article_properties(
    tags: list[dict], type: str | None = None
) -> dict[str, bool | str | None]:
    properties = {
        "in_all_news": False,
        "is_highlight": False,
        "is_liveblog": False,
        "is_active_liveblog": False,
        "is_district": False,
        "district": None,
    }

    if type == "Blog":
        properties["is_liveblog"] = True

    for tag in tags:
        tag_properties = TAG_MAPPING.get(tag.get("id"))
        if tag_properties is None:
            continue

        if tag_properties.get("boolean_column") == "in_all_news":
            properties["in_all_news"] = True
        if tag_properties.get("boolean_column") == "is_highlight":
            properties["is_highlight"] = True
        if tag_properties.get("boolean_column") == "is_active_liveblog":
            properties["is_active_liveblog"] = True
        district = tag_properties.get("district")
        if isinstance(district, str):
            properties["is_district"] = True
            properties["district"] = district

    return properties


def get_body_from_content(content: list[dict], foreign_id: int) -> str:
    body = ""
    for item in content:
        if "rows" in item:
            for row in item["rows"]:
                for c in row.get("content", []):
                    body += c.get("content", "")

    # remove any drupal-media tags from the body
    if "drupal-media" in body:
        logger.info(
            "There is a drupal media tag in the article body",
            extra={"foreign_id": foreign_id},
        )
        body = re.sub(
            r"<drupal-media[^>]*>.*?</drupal-media>", "", body, flags=re.DOTALL
        )
    return body


def get_liveblog_messages(blog_entries: list[dict]) -> list[dict]:

    messages = []

    for entry in blog_entries:
        title = entry.get("title")
        date_string = entry.get("dateTime")
        body = "".join(
            decode_and_strip_outer_div(content.get("text"))
            for content in (entry.get("content") or [])
        )

        image_information = next(
            (
                image
                for content in entry.get("content") or []
                for image in content.get("image") or []
            ),
            {},
        )

        messages.append(
            {
                "title": title,
                "creation_datetime": date_string,
                "body": body,
                "image": {
                    "url": construct_image_url(image_information.get("src"))
                    if image_information.get("src")
                    else None,
                    "alt": image_information.get("alt"),
                    "description": image_information.get("description"),
                }
                if image_information
                else None,
            }
        )
    return messages


def decode_and_strip_outer_div(input_str: str | None) -> str:
    if not input_str:
        return ""
    decoded = html.unescape(input_str)
    match = re.match(r"^\s*<div[^>]*>(.*)</div>\s*$", decoded, re.DOTALL)
    if match:
        return match.group(1)
    return decoded


def construct_image_url(image_source: str) -> str:
    return urljoin(settings.DVO_URL, image_source)
