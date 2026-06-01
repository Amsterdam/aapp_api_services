from unittest.mock import patch

from aioresponses import aioresponses
from django.core.management import call_command
from django.test import TestCase, override_settings

from news.management.commands import runnewsetl
from news.models import LiveBlogItem, LiveBlogItemImage, NewsArticle, NewsArticleImage
from news.tests.mock_data import item_article, item_liveblog
from notification.models import ScheduledNotification


class RunNewsETLTest(TestCase):
    databases = ["default", "notification"]

    @patch(
        "news.management.commands.runnewsetl.data_loader.image_set_service.get_or_upload_from_url"
    )
    def test_run_news_etl_full_pipeline(self, mock_get_or_upload_from_url):
        """Run extract, transform and load via command with patched external dependencies."""

        mock_get_or_upload_from_url.return_value = {
            "id": 12345,
            "identifier": "xyz789abc123",
            "description": "description of the image",
            "variants": [
                {
                    "image": "https://example.com/image.jpg",
                    "width": 123,
                    "height": 456,
                },
                {
                    "image": "https://example.com/image-1.jpg",
                    "width": 234,
                    "height": 567,
                },
            ],
        }

        mocked_sources = [
            {"index": "highlighted", "type": "highlight", "district": None},
            {"index": "liveblogs", "type": "liveblog", "district": None},
        ]

        highlighted_list_payload = {
            "items": [
                {
                    "id": 123123,
                    "created": item_article.MOCK_RESPONSE_123123["created"],
                    "modified": item_article.MOCK_RESPONSE_123123["modified"],
                    "publicationDate": item_article.MOCK_RESPONSE_123123[
                        "publicationDate"
                    ],
                    "image_url": item_article.MOCK_RESPONSE_123123["image_url"],
                    "is_active_liveblog": False,
                }
            ],
            "total": 1,
            "page": 0,
            "per_page": 25,
            "pages": 1,
        }
        liveblogs_list_payload = {
            "items": [
                {
                    "id": item_liveblog.MOCK_RESPONSE["id"],
                    "created": item_liveblog.MOCK_RESPONSE["created"],
                    "modified": item_liveblog.MOCK_RESPONSE["modified"],
                    "publicationDate": item_liveblog.MOCK_RESPONSE["publicationDate"],
                    "image_url": item_liveblog.MOCK_RESPONSE["image_url"],
                    "is_active_liveblog": True,
                }
            ],
            "total": 1,
            "page": 0,
            "per_page": 25,
            "pages": 1,
        }

        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}highlighted?page=0",
                    payload=highlighted_list_payload,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}liveblogs?page=0",
                    payload=liveblogs_list_payload,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_article.MOCK_RESPONSE_123123['id']}",
                    payload=item_article.MOCK_RESPONSE_123123,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_liveblog.MOCK_RESPONSE['id']}",
                    payload=item_liveblog.MOCK_RESPONSE,
                )

                call_command("runnewsetl")

        self.assertEqual(NewsArticle.objects.count(), 2)

        article = NewsArticle.objects.get(
            foreign_id=item_article.MOCK_RESPONSE_123123["id"]
        )
        liveblog_article = NewsArticle.objects.get(
            foreign_id=item_liveblog.MOCK_RESPONSE["id"]
        )

        self.assertEqual(article.type, "highlight")
        self.assertEqual(
            article.title,
            "Award voor Amsterdam: 44% vrouwen in de top",
        )
        self.assertEqual(article.url, item_article.MOCK_RESPONSE_123123["url"])
        self.assertIn("Lorem ipsum", article.body)

        self.assertEqual(liveblog_article.type, "liveblog")
        self.assertEqual(liveblog_article.url, item_liveblog.MOCK_RESPONSE["url"])
        self.assertIsNone(liveblog_article.body)

        self.assertEqual(
            LiveBlogItem.objects.filter(article=liveblog_article).count(), 19
        )
        self.assertEqual(NewsArticleImage.objects.count(), 4)
        self.assertEqual(LiveBlogItemImage.objects.count(), 18)

        self.assertTrue(
            NewsArticleImage.objects.filter(
                uri="https://example.com/image.jpg"
            ).exists()
        )
        self.assertTrue(
            LiveBlogItemImage.objects.filter(
                uri="https://example.com/image.jpg"
            ).exists()
        )

        # Assert notification was created
        self.assertEqual(ScheduledNotification.objects.count(), 1)
        active_liveblog = NewsArticle.objects.filter(is_active_liveblog=True).first()
        self.assertIsNotNone(active_liveblog.liveblog_notification_send)

    @override_settings(ENABLE_LIVEBLOG_NOTIFICATIONS=False)
    @patch(
        "news.management.commands.runnewsetl.data_loader.image_set_service.get_or_upload_from_url"
    )
    def test_run_news_etl_skips_liveblog_notifications_when_disabled(
        self, mock_get_or_upload_from_url
    ):
        mock_get_or_upload_from_url.return_value = {
            "id": 12345,
            "identifier": "xyz789abc123",
            "description": "description of the image",
            "variants": [
                {
                    "image": "https://example.com/image.jpg",
                    "width": 123,
                    "height": 456,
                },
                {
                    "image": "https://example.com/image-1.jpg",
                    "width": 234,
                    "height": 567,
                },
            ],
        }

        mocked_sources = [
            {"index": "highlighted", "type": "highlight", "district": None},
            {"index": "liveblogs", "type": "liveblog", "district": None},
        ]

        highlighted_list_payload = {
            "items": [
                {
                    "id": 123123,
                    "created": item_article.MOCK_RESPONSE_123123["created"],
                    "modified": item_article.MOCK_RESPONSE_123123["modified"],
                    "publicationDate": item_article.MOCK_RESPONSE_123123[
                        "publicationDate"
                    ],
                    "image_url": item_article.MOCK_RESPONSE_123123["image_url"],
                    "is_active_liveblog": False,
                }
            ],
            "total": 1,
            "page": 0,
            "per_page": 25,
            "pages": 1,
        }
        liveblogs_list_payload = {
            "items": [
                {
                    "id": item_liveblog.MOCK_RESPONSE["id"],
                    "created": item_liveblog.MOCK_RESPONSE["created"],
                    "modified": item_liveblog.MOCK_RESPONSE["modified"],
                    "publicationDate": item_liveblog.MOCK_RESPONSE["publicationDate"],
                    "image_url": item_liveblog.MOCK_RESPONSE["image_url"],
                    "is_active_liveblog": True,
                }
            ],
            "total": 1,
            "page": 0,
            "per_page": 25,
            "pages": 1,
        }

        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}highlighted?page=0",
                    payload=highlighted_list_payload,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}liveblogs?page=0",
                    payload=liveblogs_list_payload,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_article.MOCK_RESPONSE_123123['id']}",
                    payload=item_article.MOCK_RESPONSE_123123,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_liveblog.MOCK_RESPONSE['id']}",
                    payload=item_liveblog.MOCK_RESPONSE,
                )

                call_command("runnewsetl")

        active_liveblogs = NewsArticle.objects.filter(is_active_liveblog=True)
        self.assertEqual(active_liveblogs.count(), 1)
        self.assertIsNotNone(active_liveblogs.first().liveblog_notification_send)
        self.assertEqual(ScheduledNotification.objects.count(), 0)
