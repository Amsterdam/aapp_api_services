import datetime
import html
import logging
import re

from bs4 import BeautifulSoup
from django.utils import timezone

from news.serializers.article_serializers import NewsArticleTransformSerializer

logger = logging.getLogger(__name__)


def transform(extracted_data: list[dict]) -> list[dict]:
    """
    Transform the extracted news articles data into a list of transformed articles (dicts).
    - Cleans 'body' and text fields
    - Deduplicates by id
    - Logs and skips invalid articles
    """
    seen_ids = set()
    transformed = []
    for article in extracted_data:
        article_id = article.get("id")
        url = article.get("url")

        # Validate required fields
        if not validate_article(article):
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

        is_liveblog = (
            article.get("is_liveblog", False) or article.get("type") == "liveblog"
        )

        # Clean and transform fields
        transformed.append(
            {
                "foreign_id": article_id,
                "title": decode_and_strip_outer_div(article.get("title")),
                "body": parse_article_messages(article.get("body"))
                if not is_liveblog
                else parse_liveblog_messages(article.get("body")),
                "summary": decode_and_strip_outer_div(article.get("summary")),
                "intro": decode_and_strip_outer_div(article.get("intro")),
                "type": article.get("type"),
                "in_all_news": article.get("in_all_news", False),
                "is_highlight": article.get("is_highlight", False),
                "is_liveblog": article.get("is_liveblog", False),
                "is_district": article.get("is_district", False),
                "district": article.get("district"),
                "url": url,
                "creation_datetime": article.get("created"),
                "modification_datetime": article.get("modified"),
                "publication_datetime": article.get("publicationDate"),
                "expiration_datetime": article.get("expirationDate"),
                "image_url": article.get("image_url"),
                "is_active_liveblog": article.get("is_active_liveblog", False),
            }
        )
    return transformed


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
        image_url, image_desc = extract_first_image_from_elements(elements)
        body = extract_body_from_elements(elements, title)

        messages.append(
            {
                "title": title,
                "creation_datetime": date_string,
                "body": body,
                "image_url": image_url,
                "image_description": image_desc,
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


def extract_first_image_from_elements(elements) -> tuple[str | None, str | None]:
    """
    For now we assume that each liveblog item only contains one image.
    Find the first image in the elements and return its URL and description (alt text).
    """
    image_url = None
    image_desc = None
    for el in elements:
        img = el.find("img") if el else None
        if img and img.get("src"):
            image_url = img["src"]
            image_desc = img.get("alt", "")
            break
        # Also check if the element itself is an img
        if el and el.name == "img" and el.get("src"):
            image_url = el["src"]
            image_desc = el.get("alt", "")
            break
    return image_url, image_desc


def extract_body_from_elements(elements, title) -> str:
    """
    Build the body HTML by concatenating the HTML of all elements, but skip the title element if it
    matches the provided title.

    Also remove the image tags from the body, since we are storing the first image separately.
    """
    body_html = ""
    for el in elements:
        if el.name in ["h3", "h4"] and el.get_text(strip=True) == title:
            continue
        if el.name == "img":
            continue

        # Remove nested image tags (e.g., <p><img ... /></p>) from body content.
        el_copy = BeautifulSoup(str(el), "html.parser")
        for img in el_copy.find_all("img"):
            img.decompose()
        body_html += str(el_copy)

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
