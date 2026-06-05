from unittest.mock import patch

from aioresponses import aioresponses
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker

from news.management.commands import runnewsetl
from news.models import LiveBlogItem, LiveBlogItemImage, NewsArticle, NewsArticleImage
from news.tests.mock_data import highlighted, item_article, item_liveblog, liveblogs
from notification.models import ScheduledNotification


class RunNewsETLTest(TestCase):
    databases = ["default", "notification"]

    def _mock_single_highlight_pipeline(self, mocked):
        highlighted_list_payload = {
            "items": [
                {
                    "id": item_article.MOCK_RESPONSE_123123["id"],
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
        mocked.get(
            f"{runnewsetl.IPROX_ARTICLES_URL}highlighted?page=0",
            payload=highlighted_list_payload,
        )
        mocked.get(
            f"{runnewsetl.IPROX_DETAIL_URL}{item_article.MOCK_RESPONSE_123123['id']}",
            payload=item_article.MOCK_RESPONSE_123123,
        )

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
            {
                "index": "highlighted",
                "type": "highlight",
                "boolean_column": "is_highlight",
                "district": None,
            },
            {
                "index": "liveblogs",
                "type": "liveblog",
                "boolean_column": "is_liveblog",
                "district": None,
            },
        ]

        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}highlighted?page=0",
                    payload=highlighted.MOCK_RESPONSE,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}liveblogs?page=0",
                    payload=liveblogs.MOCK_RESPONSE,
                )
                # responses for highlighted articles
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_article.MOCK_RESPONSE_123123['id']}",
                    payload=item_article.MOCK_RESPONSE_123123,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_article.MOCK_RESPONSE_123124['id']}",
                    payload=item_article.MOCK_RESPONSE_123124,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_article.MOCK_RESPONSE_100000['id']}",
                    payload=item_article.MOCK_RESPONSE_100000,
                )
                # responses for liveblog articles
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_liveblog.MOCK_RESPONSE_1234123['id']}",
                    payload=item_liveblog.MOCK_RESPONSE_1234123,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_liveblog.MOCK_RESPONSE_1321235['id']}",
                    payload=item_liveblog.MOCK_RESPONSE_1321235,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_liveblog.MOCK_RESPONSE_1000001['id']}",
                    payload=item_liveblog.MOCK_RESPONSE_1000001,
                )

                call_command("runnewsetl")

        self.assertEqual(NewsArticle.objects.count(), 6)

        article = NewsArticle.objects.get(
            foreign_id=item_article.MOCK_RESPONSE_123123["id"]
        )
        liveblog_article = NewsArticle.objects.get(
            foreign_id=item_liveblog.MOCK_RESPONSE_1234123["id"]
        )

        self.assertEqual(article.type, "highlight")
        self.assertEqual(
            article.title,
            "Award voor Amsterdam: 44% vrouwen in de top",
        )
        self.assertEqual(article.url, item_article.MOCK_RESPONSE_123123["url"])
        self.assertIn("Lorem ipsum", article.body)

        self.assertEqual(liveblog_article.type, "liveblog")
        self.assertEqual(
            liveblog_article.url, item_liveblog.MOCK_RESPONSE_1234123["url"]
        )
        self.assertIsNone(liveblog_article.body)

        self.assertEqual(
            LiveBlogItem.objects.filter(article=liveblog_article).count(), 19
        )
        self.assertEqual(NewsArticleImage.objects.count(), 10)
        self.assertEqual(LiveBlogItemImage.objects.count(), 36)

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

    def test_run_news_etl_no_extracted_data(self):
        """Test that the ETL process runs without errors when the Iprox API returns no articles."""

        mocked_sources = [
            {
                "index": "highlighted",
                "type": "highlight",
                "boolean_column": "is_highlight",
                "district": None,
            },
            {
                "index": "liveblogs",
                "type": "liveblog",
                "boolean_column": "is_liveblog",
                "district": None,
            },
        ]

        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}highlighted?page=0",
                    payload={
                        "items": [],
                        "total": 0,
                        "page": 0,
                        "per_page": 25,
                        "pages": 1,
                    },
                )
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}liveblogs?page=0",
                    payload={
                        "items": [],
                        "total": 0,
                        "page": 0,
                        "per_page": 25,
                        "pages": 1,
                    },
                )

                call_command("runnewsetl")

        self.assertEqual(NewsArticle.objects.count(), 0)
        self.assertEqual(LiveBlogItem.objects.count(), 0)
        self.assertEqual(NewsArticleImage.objects.count(), 0)
        self.assertEqual(LiveBlogItemImage.objects.count(), 0)

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
            {
                "index": "highlighted",
                "type": "highlight",
                "boolean_column": "is_highlight",
                "district": None,
            },
            {
                "index": "liveblogs",
                "type": "liveblog",
                "boolean_column": "is_liveblog",
                "district": None,
            },
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
                    "id": item_liveblog.MOCK_RESPONSE_1234123["id"],
                    "created": item_liveblog.MOCK_RESPONSE_1234123["created"],
                    "modified": item_liveblog.MOCK_RESPONSE_1234123["modified"],
                    "publicationDate": item_liveblog.MOCK_RESPONSE_1234123[
                        "publicationDate"
                    ],
                    "image_url": item_liveblog.MOCK_RESPONSE_1234123["image_url"],
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
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_liveblog.MOCK_RESPONSE_1234123['id']}",
                    payload=item_liveblog.MOCK_RESPONSE_1234123,
                )

                call_command("runnewsetl")

        active_liveblogs = NewsArticle.objects.filter(is_active_liveblog=True)
        self.assertEqual(active_liveblogs.count(), 1)
        self.assertIsNotNone(active_liveblogs.first().liveblog_notification_send)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    @override_settings(
        DELETE_UNSEEN_ARTICLES=True,
        DELETE_UNSEEN_ARTICLES_AFTER_SECONDS=7200,
        ENABLE_LIVEBLOG_NOTIFICATIONS=False,
    )
    @patch("news.management.commands.runnewsetl.logger.info")
    @patch(
        "news.management.commands.runnewsetl.data_loader.image_set_service.get_or_upload_from_url"
    )
    def test_run_news_etl_marks_stale_articles_deleted_when_enabled(
        self, mock_get_or_upload_from_url, mock_logger_info
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
                }
            ],
        }
        stale_article = baker.make(
            NewsArticle,
            foreign_id=999999,
            deleted=False,
            type="article",
        )
        NewsArticle.objects.filter(id=stale_article.id).update(
            last_seen=timezone.now() - timezone.timedelta(hours=3)
        )

        mocked_sources = [
            {
                "index": "highlighted",
                "type": "highlight",
                "boolean_column": "is_highlight",
                "district": None,
            }
        ]
        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                self._mock_single_highlight_pipeline(mocked)
                call_command("runnewsetl")

        stale_article.refresh_from_db()
        fetched_article = NewsArticle.objects.get(
            foreign_id=item_article.MOCK_RESPONSE_123123["id"]
        )

        self.assertTrue(stale_article.deleted)
        self.assertFalse(fetched_article.deleted)
        mock_logger_info.assert_any_call(
            "News garbage collector completed.",
            extra={"deleted_count": 1},
        )

    @override_settings(
        DELETE_UNSEEN_ARTICLES=False,
        DELETE_UNSEEN_ARTICLES_AFTER_SECONDS=7200,
        ENABLE_LIVEBLOG_NOTIFICATIONS=False,
    )
    @patch(
        "news.management.commands.runnewsetl.data_loader.image_set_service.get_or_upload_from_url"
    )
    def test_run_news_etl_skips_garbage_collection_when_disabled(
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
                }
            ],
        }
        stale_article = baker.make(
            NewsArticle,
            foreign_id=999999,
            deleted=False,
            type="article",
        )
        NewsArticle.objects.filter(id=stale_article.id).update(
            last_seen=timezone.now() - timezone.timedelta(hours=3)
        )

        mocked_sources = [
            {
                "index": "highlighted",
                "type": "highlight",
                "boolean_column": "is_highlight",
                "district": None,
            }
        ]
        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                self._mock_single_highlight_pipeline(mocked)
                call_command("runnewsetl")

        stale_article.refresh_from_db()
        self.assertFalse(stale_article.deleted)

    @patch(
        "news.management.commands.runnewsetl.data_loader.image_set_service.get_or_upload_from_url"
    )
    def test_run_news_etl_two_boolean_columns_set_to_true(
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
            {
                "index": "all_news",
                "type": "article",
                "boolean_column": "in_all_news",
                "district": None,
            },
            {
                "index": "highlighted",
                "type": "highlight",
                "boolean_column": "is_highlight",
                "district": None,
            },
        ]

        all_news_list_payload = {
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

        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}all_news?page=0",
                    payload=all_news_list_payload,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}highlighted?page=0",
                    payload=highlighted_list_payload,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}{item_article.MOCK_RESPONSE_123123['id']}",
                    payload=item_article.MOCK_RESPONSE_123123,
                )

                call_command("runnewsetl")

        self.assertEqual(NewsArticle.objects.count(), 1)
        article = NewsArticle.objects.first()
        self.assertTrue(article.in_all_news)
        self.assertTrue(article.is_highlight)

    def test_run_news_etl_change_type_existing_item(self):
        """Test that when an existing item changes type, the old record is updated to get a new type.
        This could happen if an article is first a highlight but then not anymore (just an article)
        """

        baker.make(
            NewsArticle,
            foreign_id=123123,
            type="highlight",
            is_highlight=True,
            in_all_news=True,
        )

        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(NewsArticle.objects.first().type, "highlight")

        # Simulate the article changing type in the Iprox API
        mocked_sources = [
            {
                "index": "all_news",
                "type": "article",
                "boolean_column": "in_all_news",
                "district": None,
            },
            {
                "index": "highlighted",
                "type": "highlight",
                "boolean_column": "is_highlight",
                "district": None,
            },
        ]
        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}all_news?page=0",
                    payload={
                        "items": [
                            {
                                "id": 123123,
                                "created": item_article.MOCK_RESPONSE_123123["created"],
                                "modified": item_article.MOCK_RESPONSE_123123[
                                    "modified"
                                ],
                                "publicationDate": item_article.MOCK_RESPONSE_123123[
                                    "publicationDate"
                                ],
                                "image_url": item_article.MOCK_RESPONSE_123123[
                                    "image_url"
                                ],
                                "is_active_liveblog": False,
                            }
                        ],
                        "total": 1,
                        "page": 0,
                        "per_page": 25,
                        "pages": 1,
                    },
                )
                mocked.get(
                    f"{runnewsetl.IPROX_ARTICLES_URL}highlighted?page=0",
                    payload={
                        "items": [
                            {
                                "id": 100000,
                                "created": item_article.MOCK_RESPONSE_100000["created"],
                                "modified": item_article.MOCK_RESPONSE_100000[
                                    "modified"
                                ],
                                "publicationDate": item_article.MOCK_RESPONSE_100000[
                                    "publicationDate"
                                ],
                                "image_url": item_article.MOCK_RESPONSE_100000[
                                    "image_url"
                                ],
                                "is_active_liveblog": False,
                            }
                        ],
                        "total": 1,
                        "page": 0,
                        "per_page": 25,
                        "pages": 1,
                    },
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}123123",
                    payload=item_article.MOCK_RESPONSE_123123,
                )
                mocked.get(
                    f"{runnewsetl.IPROX_DETAIL_URL}100000",
                    payload=item_article.MOCK_RESPONSE_100000,
                )

                call_command("runnewsetl")

        self.assertEqual(
            NewsArticle.objects.count(), 2
        )  # 123123 should be updated to article, and 100000 should be created
        self.assertEqual(NewsArticle.objects.first().type, "article")
        self.assertTrue(NewsArticle.objects.first().in_all_news)
        self.assertFalse(NewsArticle.objects.first().is_highlight)
