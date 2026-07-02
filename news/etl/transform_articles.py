import datetime
import html
import logging
import re

from bs4 import BeautifulSoup
from django.utils import timezone

from news.serializers.article_serializers import NewsArticleTransformSerializer

logger = logging.getLogger(__name__)

ARTICLE_SOURCE_DEFAULTS = {
    "district": None,
    "in_all_news": False,
    "is_highlight": False,
    "is_liveblog": False,
    "is_district": False,
    "is_construction_work": False,
}


def transform_articles(extracted_data: list[dict]) -> list[dict]:
    """
    Transform the extracted news articles data into a list of transformed articles (dicts).
    - Cleans 'body' and text fields
    - Deduplicates by id
    - Logs and skips invalid articles
    """
    seen_ids = set()
    transformed = []
    for article in extracted_data:
        normalized_article = normalize_article(article)
        article_id = normalized_article.get("id")

        # Validate required fields
        if not validate_article(normalized_article):
            logger.warning(
                "Skipping article due to validation failure.",
                extra={"article_id": article_id},
            )
            continue

        # Deduplication by id
        if article_id in seen_ids:
            logger.warning(
                "Duplicate article ID found. Skipping duplicate.",
                extra={"article_id": article_id},
            )
            continue

        seen_ids.add(article_id)

        transformed.append(map_article_fields(normalized_article))
    return transformed


def normalize_article(article: dict) -> dict:
    return {**ARTICLE_SOURCE_DEFAULTS, **article}


def map_article_fields(article: dict) -> dict:
    return {
        "foreign_id": article.get("id"),
        "title": decode_and_strip_outer_div(article.get("title")),
        "body": parse_article_messages(article.get("body"))
        if not article.get("is_liveblog", False)
        else parse_liveblog_messages(article.get("body")),
        "summary": decode_and_strip_outer_div(article.get("summary")),
        "intro": decode_and_strip_outer_div(article.get("intro")),
        "in_all_news": article.get("in_all_news", False),
        "is_highlight": article.get("is_highlight", False),
        "is_liveblog": article.get("is_liveblog", False),
        "is_district": article.get("is_district", False),
        "is_construction_work": article.get("is_construction_work", False),
        "district": article.get("district"),
        "url": article.get("url"),
        "creation_datetime": article.get("created"),
        "modification_datetime": article.get("modified"),
        "publication_datetime": article.get("publicationDate"),
        "expiration_datetime": article.get("expirationDate"),
        "image_url": article.get("image_url"),
        "is_active_liveblog": article.get("is_active_liveblog", False),
    }


def validate_article(article: dict) -> bool:
    news_article_serializer = NewsArticleTransformSerializer(data=article)
    return news_article_serializer.is_valid()


def decode_and_strip_outer_div(input_str: str | None) -> str:
    if not input_str:
        return ""
    decoded = html.unescape(input_str)
    match = re.match(r"^\s*<div[^>]*>(.*)</div>\s*$", decoded, re.DOTALL)
    if match:
        return match.group(1)
    return decoded


def parse_article_messages(input_str: str | None) -> str:
    """
    For non-liveblog articles, we still want to clean the body content by:
     - decoding HTML entities and stripping outer divs.
     - add quotes around blockquote elements.
    """
    decoded = decode_and_strip_outer_div(input_str)
    return add_quotes_around_blockquotes(decoded)


def parse_liveblog_messages(input_str: str | None) -> list[dict]:
    decoded = decode_and_strip_outer_div(input_str)
    if not decoded:
        return []
    soup = BeautifulSoup(decoded, "html.parser")
    messages = []

    # Find all datetime <p> tags.
    # In liveblogs, each message starts with a <p class="datetime">datetime</p> tag,
    # followed by content until the next datetime tag.
    # We can use this structure to split the liveblog body into individual messages.
    datetimes = soup.find_all("p", class_="datetime")
    for dt_tag in datetimes:
        dt = dt_tag.get_text(strip=True)
        date_string = change_date_string_to_iso(dt)

        elements = find_elements_between_datetimes(dt_tag)

        title = extract_title_from_elements(elements)
        body = extract_body_from_elements(elements, title)

        messages.append(
            {
                "title": title,
                "creation_datetime": date_string,
                "body": body,
            }
        )
    return messages


def find_elements_between_datetimes(dt_tag):
    """
    Find all elements between this datetime tag and the next datetime tag.
    Uses BeautifulSoup's find_next_sibling to iterate through siblings until the next <p class="datetime"> is found.
    """
    next_sibling = dt_tag.find_next_sibling()
    elements = []
    while next_sibling and not (
        next_sibling.name == "p" and "datetime" in next_sibling.get("class", [])
    ):
        elements.append(next_sibling)
        next_sibling = next_sibling.find_next_sibling()
    return elements


def extract_title_from_elements(elements) -> str:
    """
    Find the first h3 or h4 element in the list of elements and return its text as the title.
    If no such element is found, return an empty string."""
    title = ""
    for el in elements:
        if el.name in ["h3", "h4"]:
            title = el.get_text(strip=True)
            break
    return title


def extract_body_from_elements(elements, title) -> str:
    """
    Build the body HTML by concatenating the HTML of all elements, but skip the title element if it
    matches the provided title.

    Also adds quotes around blockquote elements in the body.
    """
    body_html = ""
    for el in elements:
        if el.name in ["h3", "h4"] and el.get_text(strip=True) == title:
            continue
        body_html += str(el)

    body_html = add_quotes_around_blockquotes(body_html)
    return body_html.strip()


def add_quotes_around_blockquotes(input_str: str) -> str:
    """
    Add quotes around blockquote elements in the input HTML string.
    For example, <blockquote>Some quote</blockquote> becomes <blockquote>"Some quote"</blockquote>.
    """
    soup = BeautifulSoup(input_str, "html.parser")
    for blockquote in soup.find_all("blockquote"):
        text = blockquote.get_text()
        blockquote.string = f'"{text}"'
    return str(soup)


def change_date_string_to_iso(input_str: str) -> str:
    """
    Convert a datetime string from "DD-MM-YYYY, HH:MM" or "YYYY-MM-DD, HH:MM" format to ISO 8601
    datetime string with timezone offset (using Django's default timezone).

    Example input: "12-01-2024, 14:30" or "2024-01-12, 14:30"
    Desired output: "2024-01-12T14:30:00+01:00" (assuming default timezone is CET/CEST)
    """
    # First check which format the date string is in, then parse accordingly.
    if len(input_str.split("-")[0]) == 4:  # Format is likely "YYYY-MM-DD, HH:MM"
        datetime_format = "%Y-%m-%d, %H:%M"
    else:  # Format is likely "DD-MM-YYYY, HH:MM"
        datetime_format = "%d-%m-%Y, %H:%M"

    try:
        dt = datetime.datetime.strptime(input_str, datetime_format)
        aware_dt = timezone.make_aware(dt, timezone.get_default_timezone())
        return aware_dt.isoformat()
    except ValueError as e:
        logger.error(f"Error parsing datetime string '{input_str}': {e}")
    return input_str  # Return original string if parsing fails
