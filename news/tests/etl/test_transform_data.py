from django.test import TestCase

from news.etl.transform_data import (
    change_date_string_to_iso,
    decode_and_strip_outer_div,
    parse_liveblog_messages,
    transform,
    validate_article,
)
from news.tests.mock_data import item_article, item_liveblog


class TransformDataTest(TestCase):
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

    def test_decode_and_strip_outer_div_None(self):
        html = None
        expected = ""
        result = decode_and_strip_outer_div(html)
        self.assertEqual(result, expected)

    def test_parse_liveblog_messages(self):
        input_str = """
        <div>
            <p class="datetime">2024-01-01T12:00:00Z</p>
            <h3>First update</h3>
            <p>Details of the first update.</p>
            <img src="https://example.com/image1.jpg" alt="Image 1 description">
            <p class="datetime">2024-01-01T13:00:00Z</p>
            <h4>Second update</h4>
            <p>Details of the second update.</p>
        </div>
        """
        messages = parse_liveblog_messages(input_str)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["datetime"], "2024-01-01T12:00:00Z")
        self.assertEqual(messages[0]["title"], "First update")
        self.assertIn("Details of the first update.", messages[0]["body"])
        self.assertEqual(messages[0]["image_url"], "https://example.com/image1.jpg")
        self.assertEqual(messages[0]["image_description"], "Image 1 description")
        self.assertEqual(messages[1]["datetime"], "2024-01-01T13:00:00Z")
        self.assertEqual(messages[1]["title"], "Second update")
        self.assertIn("Details of the second update.", messages[1]["body"])
        self.assertIsNone(messages[1]["image_url"])
        self.assertIsNone(messages[1]["image_description"])

    def test_change_date_string_to_iso_valid(self):
        input_str = "12-01-2024, 14:30"
        expected = "2024-01-12T14:30:00"
        result = change_date_string_to_iso(input_str)
        self.assertEqual(result, expected)

    def test_change_date_string_to_iso_invalid(self):
        input_str = "invalid date string"
        result = change_date_string_to_iso(input_str)
        self.assertEqual(result, input_str)  # Should return original string on failure

    def test_validate_article_valid(self):
        article = {
            "id": "123",
            "title": "Test Article",
            "body": "This is a test article.",
        }
        self.assertTrue(validate_article(article))

    def test_validate_article_missing_field(self):
        article = {"id": "123", "title": "Test Article"}
        self.assertFalse(validate_article(article))

    def test_transform_item(self):
        extracted_data = [item_article.MOCK_RESPONSE_123123]
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
        extracted_data = [{**item_liveblog.MOCK_RESPONSE, **{"type": "liveblog"}}]
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

    def test_transform_deduplication(self):
        extracted_data = [
            {
                "id": "123",
                "title": "<div>Test Article</div>",
                "body": "<div>This is a test article.</div>",
                "summary": "<div>Summary</div>",
            },
            {
                # Duplicate ID
                "id": "123",
                "title": "<div>Test Article 2</div>",
                "body": "<div>This is another test article.</div>",
                "summary": "<div>Summary 2</div>",
            },
        ]
        with self.assertLogs(level="WARNING") as log:
            transformed = transform(extracted_data)
            self.assertEqual(len(transformed), 1)
            self.assertEqual(transformed[0]["foreign_id"], "123")
            self.assertIn(
                "Duplicate article ID found: 123. Skipping duplicate.", log.output[0]
            )

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
            self.assertIn(
                "Skipping article with id 123 due to validation failure.", log.output[0]
            )
