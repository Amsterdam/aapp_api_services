import datetime
import html
import logging
import re

from bs4 import BeautifulSoup

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
                f"Skipping article with id {article_id} due to validation failure."
            )
            continue

        # Deduplication by id
        if article_id in seen_ids:
            logger.warning(
                f"Duplicate article ID found: {article_id}. Skipping duplicate."
            )
            continue

        seen_ids.add(article_id)

        # Clean and transform fields
        transformed.append(
            {
                "foreign_id": article_id,
                "title": decode_and_strip_outer_div(article.get("title")),
                "body": decode_and_strip_outer_div(article.get("body"))
                if article.get("type") != "liveblog"
                else parse_liveblog_messages(article.get("body")),
                "summary": decode_and_strip_outer_div(article.get("summary")),
                "intro": decode_and_strip_outer_div(article.get("intro")),
                "type": article.get("type"),
                "district": article.get("district"),
                "url": url,
                "creation_date": article.get("created"),
                "modification_date": article.get("modified"),
                "publication_date": article.get("publicationDate"),
                "expiration_date": article.get("expirationDate"),
                "image_url": article.get("image_url"),
            }
        )
    return transformed


def validate_article(article: dict) -> bool:
    required_fields = ["id", "title", "body"]
    for field in required_fields:
        value = article.get(field)
        if not value:
            return False
    return True


def decode_and_strip_outer_div(input_str: str | None) -> str:
    if not input_str:
        return ""
    decoded = html.unescape(input_str)
    match = re.match(r"^\s*<div[^>]*>(.*)</div>\s*$", decoded, re.DOTALL)
    if match:
        return match.group(1)
    return decoded


def parse_liveblog_messages(input_str: str | None) -> list[dict]:
    decoded = decode_and_strip_outer_div(input_str)
    if not decoded:
        return []
    soup = BeautifulSoup(decoded, "html.parser")
    messages = []
    # Find all datetime <p> tags
    datetimes = soup.find_all("p", class_="datetime")
    for dt_tag in datetimes:
        dt = dt_tag.get_text(strip=True)
        date_string = change_date_string_to_iso(dt)

        # Find all elements between this datetime and the next datetime
        next_sibling = dt_tag.find_next_sibling()
        elements = []

        while next_sibling and (
            not (
                next_sibling.name == "p" and "datetime" in next_sibling.get("class", [])
            )
        ):
            elements.append(next_sibling)
            next_sibling = next_sibling.find_next_sibling()

        # Find title
        title = ""
        for el in elements:
            if el.name in ["h3", "h4"]:
                title = el.get_text(strip=True)
                break

        # Find first image anywhere in elements
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

        # Build body HTML, remove the title tag if present
        body_html = ""
        for el in elements:
            if el.name in ["h3", "h4"] and el.get_text(strip=True) == title:
                continue
            body_html += str(el)

        messages.append(
            {
                "title": title,
                "datetime": date_string,
                "body": body_html.strip(),
                "image_url": image_url,
                "image_description": image_desc,
            }
        )
    return messages


def change_date_string_to_iso(input_str: str) -> str:
    """
    Convert a datetime string from "DD-MM-YYYY, HH:MM" format to ISO 8601 format "YYYY-MM-DDTHH:MM:SS".
    Example input: "12-01-2024, 14:30"
    Desired output: "2024-01-12T14:30:00"
    """
    try:
        datetime_format = "%d-%m-%Y, %H:%M"
        dt = datetime.datetime.strptime(input_str, datetime_format)
        return dt.isoformat()
    except ValueError as e:
        logger.error(f"Error parsing datetime string '{input_str}': {e}")
        return input_str  # Return original string if parsing fails
