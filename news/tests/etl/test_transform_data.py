from bs4 import BeautifulSoup
from django.test import TestCase

from news.etl.transform_data import (
    add_quotes_around_blockquotes,
    change_date_string_to_iso,
    decode_and_strip_outer_div,
    extract_body_from_elements,
    extract_first_image_from_elements,
    extract_title_from_elements,
    find_elements_between_datetimes,
    parse_liveblog_messages,
    transform,
    validate_article,
)
from news.tests.mock_data import item_article, item_liveblog


class TransformDataTest(TestCase):
    def test_transform_item(self):
        extracted_data = [
            {
                **item_article.MOCK_RESPONSE_123123,
                **{"in_all_news": True, "district": None},
            }
        ]
        transformed = transform(extracted_data)
        self.assertEqual(len(transformed), 1)
        article = transformed[0]
        self.assertEqual(article["foreign_id"], 123123)
        self.assertEqual(
            article["title"], "Award voor Amsterdam: 44% vrouwen in de top"
        )
        self.assertEqual(
            article["summary"],
            "<p>Amsterdam streeft naar een diverse organisatie en heeft daarmee een prijs in de wacht gesleept.</p>",
        )
        self.assertEqual(
            article["url"], "https://example.com/news/highlighted/women-top/"
        )
        self.assertEqual(article["image_url"], "https://example.com/image.jpg")

    def test_transform_liveblog(self):
        extracted_data = [
            {
                **item_liveblog.MOCK_RESPONSE_1234123,
                **{"district": None, "is_liveblog": True},
            }
        ]
        transformed = transform(extracted_data)
        self.assertEqual(len(transformed), 1)
        article = transformed[0]
        self.assertEqual(article["foreign_id"], 1234123)
        self.assertEqual(
            article["title"],
            "Liveblog verkiezingen Europees Parlement en referendum Hoofdgroenstructuur 2024",
        )
        self.assertIsInstance(article["body"], list)
        self.assertEqual(len(article["body"]), 19)
        self.assertEqual(article["body"][0]["title"], "Title")
        self.assertEqual(article["body"][1]["title"], "Another title")

    def test_transform_liveblog_when_legacy_indicators_differ(self):
        extracted_data = [
            {
                **item_liveblog.MOCK_RESPONSE_1234123,
                **{
                    "district": "noord",
                    "is_liveblog": True,
                    "is_district": True,
                },
            }
        ]

        transformed = transform(extracted_data)
        self.assertEqual(len(transformed), 1)
        article = transformed[0]
        self.assertIsInstance(article["body"], list)
        self.assertTrue(article["is_liveblog"])
        self.assertTrue(article["is_district"])

    def test_transform_invalid_article(self):
        extracted_data = [
            {
                "id": "123",
                "title": "<div>Test Article</div>",
                # Missing body
                "summary": "<div>Summary</div>",
            }
        ]
        with self.assertLogs(level="WARNING") as log:
            transformed = transform(extracted_data)
            self.assertEqual(len(transformed), 0)
            self.assertIn("Skipping article due to validation failure.", log.output[0])

    def test_validate_article_valid(self):
        article = {
            "id": "123",
            "title": "Test Article",
            "body": "This is a test article.",
            "in_all_news": True,
            "district": None,
            "url": "https://example.com/test-article",
            "publicationDate": "2024-01-01T12:00:00Z",
        }
        self.assertTrue(validate_article(article))

    def test_validate_article_missing_field(self):
        article = {"id": "123", "title": "Test Article"}
        self.assertFalse(validate_article(article))

    def test_decode_and_strip_outer_div(self):
        html = item_article.MOCK_RESPONSE_123123["summary"]
        expected = "<p>Amsterdam streeft naar een diverse organisatie en heeft daarmee een prijs in de wacht gesleept.</p>"
        result = decode_and_strip_outer_div(html)
        self.assertEqual(result, expected)

    def test_decode_and_strip_outer_div_no_div(self):
        html = "<p>This is a test.</p>"
        expected = "<p>This is a test.</p>"
        result = decode_and_strip_outer_div(html)
        self.assertEqual(result, expected)

    def test_decode_and_strip_outer_div_other_tags_remain(self):
        html = "<div><p>This is a <strong>test</strong>.</p></div>"
        expected = "<p>This is a <strong>test</strong>.</p>"
        result = decode_and_strip_outer_div(html)
        self.assertEqual(result, expected)

    def test_add_quotes_around_blockquotes(self):
        html = "<div><blockquote>This is a quote.</blockquote></div>"
        expected = '<div><blockquote>"This is a quote."</blockquote></div>'
        result = add_quotes_around_blockquotes(html)
        self.assertEqual(result, expected)

    def test_decode_and_strip_outer_div_None(self):
        html = None
        expected = ""
        result = decode_and_strip_outer_div(html)
        self.assertEqual(result, expected)

    def test_parse_liveblog_messages(self):
        input_str = """
        <div>
            <p class="datetime">2024-01-01, 12:00</p>
            <h3>First update</h3>
            <p>Details of the first update.</p>
            <img src="https://example.com/image1.jpg" alt="Image 1 description">
            <p class="datetime">2024-01-01, 13:00</p>
            <h4>Second update</h4>
            <p>Details of the second update.</p>
        </div>
        """
        messages = parse_liveblog_messages(input_str)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["creation_datetime"], "2024-01-01T12:00:00+01:00")
        self.assertEqual(messages[0]["title"], "First update")
        self.assertNotIn(
            "<img", messages[0]["body"]
        )  # Image should be removed from body
        self.assertIn("Details of the first update.", messages[0]["body"])
        self.assertEqual(messages[0]["image_url"], "https://example.com/image1.jpg")
        self.assertEqual(messages[0]["image_description"], "Image 1 description")
        self.assertEqual(messages[1]["creation_datetime"], "2024-01-01T13:00:00+01:00")
        self.assertEqual(messages[1]["title"], "Second update")
        self.assertIn("Details of the second update.", messages[1]["body"])
        self.assertIsNone(messages[1]["image_url"])
        self.assertIsNone(messages[1]["image_description"])

    def test_parse_liveblog_messages_image_nesting(self):
        input_str = """
        <div>
            <p class="datetime">2024-06-09, 23:03</p>
            <h3 id="a3"><strong>Derde titel</strong></h3>
            <p>Eerste deel tekst.</p>
            <p>
                <img src="https://www.example.com/image1.jpg" width="609" data-sources="[{&quot;width&quot;:80,&quot;height&quot;:80,&quot;src&quot;:&quot;/publish/pages/1072780/80px/ep_2024_corr.jpg&quot;,&quot;sizeClass&quot;:&quot;size_80px&quot;},{&quot;width&quot;:220,&quot;height&quot;:220,&quot;src&quot;:&quot;/publish/pages/1072780/220px/ep_2024_corr.jpg&quot;,&quot;sizeClass&quot;:&quot;size_220px&quot;},{&quot;width&quot;:609,&quot;height&quot;:609,&quot;src&quot;:&quot;/publish/pages/1072780/ep_2024_corr.jpg&quot;}]" height="609" data-id="1072780" alt="" id="img_pagvld_23966763_0" class="img_pagvld_23966763_0" resolved="true" />
            </p>
            <p>Tweede deel tekst.</p>
            <p>Derde deel tekst.</p>
            <p class="Calltoaction-blauw">
                <a href="https://example.com/action-punt" class="externLink">Meer over de voorlopige uitslag</a>
            </p>
        </div>
        """
        messages = parse_liveblog_messages(input_str)
        self.assertEqual(len(messages), 1)

        self.assertNotIn(
            "<img", messages[0]["body"]
        )  # Image should be removed from body
        self.assertIn("Eerste deel tekst.", messages[0]["body"])
        self.assertIn("Tweede deel tekst.", messages[0]["body"])
        self.assertIn("Derde deel tekst.", messages[0]["body"])
        self.assertEqual(messages[0]["image_url"], "https://www.example.com/image1.jpg")
        self.assertEqual(messages[0]["image_description"], "")

    def test_find_elements_between_datetimes(self):
        html = """<div>
            <p class="datetime">2024-01-01, 12:00</p>
            <h3>First update</h3>
            <p>Details of the first update.</p>
            <img src="https://example.com/image1.jpg" alt="Image 1 description">
            <p class="datetime">2024-01-01, 13:00</p>
            <h4>Second update</h4>
            <p>Details of the second update.</p>
        </div>"""
        soup = BeautifulSoup(html, "html.parser")
        datetimes = soup.find_all("p", class_="datetime")
        elements = find_elements_between_datetimes(datetimes[0])
        self.assertEqual(len(elements), 3)
        self.assertEqual(elements[0].name, "h3")
        self.assertEqual(elements[1].name, "p")
        self.assertEqual(elements[2].name, "img")

    def test_extract_title_from_elements(self):
        html = "<h3>My Title</h3><p>Body</p>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        title = extract_title_from_elements(elements)
        self.assertEqual(title, "My Title")

    def test_extract_title_from_elements_no_title(self):
        html = "<p>Body</p>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        title = extract_title_from_elements(elements)
        self.assertEqual(title, "")

    def test_extract_first_image_from_elements(self):
        html = '<p>Body</p><img src="img.jpg" alt="desc">'
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        url, desc = extract_first_image_from_elements(elements)
        self.assertEqual(url, "img.jpg")
        self.assertEqual(desc, "desc")

    def test_extract_first_image_from_elements_no_image(self):
        html = "<p>Body</p>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        url, desc = extract_first_image_from_elements(elements)
        self.assertIsNone(url)
        self.assertIsNone(desc)

    def test_extract_body_from_elements(self):
        html = "<h3>Title</h3><p>Body</p>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        body = extract_body_from_elements(elements, "Title")
        self.assertNotIn("Title", body)
        self.assertIn("Body", body)

    def test_extract_body_from_elements_no_title_to_skip(self):
        html = "<p>Body</p>"
        soup = BeautifulSoup(html, "html.parser")
        elements = list(soup.children)
        body = extract_body_from_elements(elements, "")
        self.assertIn("Body", body)

    def test_change_date_string_to_iso_valid(self):
        input_str = "12-01-2024, 14:30"
        expected = "2024-01-12T14:30:00+01:00"
        result = change_date_string_to_iso(input_str)
        self.assertEqual(result, expected)

    def test_change_date_string_to_iso_invalid(self):
        input_str = "invalid date string"
        result = change_date_string_to_iso(input_str)
        self.assertEqual(result, input_str)  # Should return original string on failure
