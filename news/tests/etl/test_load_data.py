from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker
from requests.exceptions import ConnectionError, HTTPError

from core.services.notification_service import ScheduledNotification
from news.etl.load_data import NewsArticleLoader, garbage_collect_unseen_articles
from news.models import (
    LiveBlogItem,
    LiveBlogItemImage,
    LiveblogNotification,
    NewsArticle,
    NewsArticleImage,
)


class LoadDataTest(TestCase):
    databases = {"default", "notification"}

    def setUp(self):
        self.loader = NewsArticleLoader()

    def _set_mock_image_set_service_side_effect(self, mock_image_set_service):
        mock_image_set_service.return_value.get_or_upload_from_url.side_effect = [
            {
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
                    {
                        "image": "https://example.com/image-2.jpg",
                        "width": 345,
                        "height": 678,
                    },
                ],
            }
        ]
        loader = NewsArticleLoader(
            image_set_service=mock_image_set_service.return_value
        )
        return loader

    @patch("news.etl.load_data.ImageSetService")
    def test_load(self, mock_image_set_service):
        transformed_data = [
            {
                "foreign_id": "123123",
                "title": "Test Article",
                "url": "https://example.com/test-article",
                "modification_datetime": "2024-01-01T12:00:00Z",
                "image": {
                    "url": "https://example.com/image.jpg",
                    "alt": "Alt text for the image",
                    "description": "Description of the image",
                },
                "in_all_news": True,
                "is_liveblog": False,
                "is_highlight": False,
                "is_district": False,
                "creation_datetime": "2024-01-01T12:00:00Z",
                "publication_datetime": "2024-01-01T12:00:00Z",
                "expiration_datetime": None,
            }
        ]
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)
        loader.load(transformed_data)
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(
            NewsArticle.objects.first().title, transformed_data[0]["title"]
        )
        self.assertFalse(NewsArticle.objects.first().deleted)
        self.assertEqual(NewsArticleImage.objects.count(), 3)

    @override_settings(ENABLE_LIVEBLOG_NOTIFICATIONS=True)
    @patch("news.etl.load_data.NewLiveblogNotificationService")
    def test_load_sends_notification_for_new_active_liveblog(
        self, mock_notification_service
    ):
        liveblog_data = {
            "foreign_id": "123123",
            "title": "New liveblog",
            "url": "https://example.com/liveblog",
            "is_liveblog": True,
            "is_active_liveblog": True,
            "creation_datetime": "2024-01-01T12:00:00Z",
            "modification_datetime": "2024-01-01T12:00:00Z",
            "publication_datetime": "2024-01-01T12:00:00Z",
            "expiration_datetime": None,
            "liveblog_messages": [],
        }

        self.loader.load([liveblog_data])

        liveblog = NewsArticle.objects.get(foreign_id=liveblog_data["foreign_id"])
        mock_notification_service.return_value.send.assert_called_once_with(
            liveblog_id=liveblog.id,
            liveblog_title=liveblog_data["title"],
        )
        self.assertIsNotNone(liveblog.liveblog_notification_send)

        self.loader.load([liveblog_data])
        mock_notification_service.return_value.send.assert_called_once()

    @patch("news.etl.load_data.ImageSetService")
    def test_load_continues_when_image_upload_fails(self, mock_image_set_service):
        transformed_data = [
            {
                "foreign_id": "123123",
                "title": "Broken image article",
                "url": "https://example.com/test-article-1",
                "modification_datetime": "2024-01-01T12:00:00Z",
                "image": {
                    "url": "https://example.com/image.jpg",
                    "alt": "Alt text for the image",
                    "description": "Description of the image",
                },
                "in_all_news": True,
                "is_liveblog": False,
                "is_highlight": False,
                "is_district": False,
                "creation_datetime": "2024-01-01T12:00:00Z",
                "publication_datetime": "2024-01-01T12:00:00Z",
                "expiration_datetime": None,
            },
            {
                "foreign_id": "123124",
                "title": "Working image article",
                "url": "https://example.com/test-article-2",
                "modification_datetime": "2024-01-01T12:00:00Z",
                "image": {
                    "url": "https://example.com/image-2.jpg",
                    "alt": "Alt text for second image",
                    "description": "Description of second image",
                },
                "in_all_news": True,
                "is_liveblog": False,
                "is_highlight": False,
                "is_district": False,
                "creation_datetime": "2024-01-01T12:00:00Z",
                "publication_datetime": "2024-01-01T12:00:00Z",
                "expiration_datetime": None,
            },
        ]
        mock_image_set_service.return_value.get_or_upload_from_url.side_effect = [
            ConnectionError("Upload timed out"),
            {
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
                    {
                        "image": "https://example.com/image-2.jpg",
                        "width": 345,
                        "height": 678,
                    },
                ],
            },
        ]

        loader = NewsArticleLoader(
            image_set_service=mock_image_set_service.return_value
        )

        loader.load(transformed_data)

        self.assertEqual(NewsArticle.objects.count(), 2)
        self.assertEqual(NewsArticleImage.objects.count(), 3)
        self.assertTrue(NewsArticle.objects.filter(foreign_id="123124").exists())
        self.assertTrue(
            NewsArticleImage.objects.filter(article__foreign_id="123124").exists()
        )

    @patch("news.etl.load_data.ImageSetService")
    def test_load_continues_when_image_upload_fails_completely(
        self, mock_image_set_service
    ):
        transformed_data = [
            {
                "foreign_id": "123123",
                "title": "Broken image article",
                "url": "https://example.com/test-article-1",
                "modification_datetime": "2024-01-01T12:00:00Z",
                "image": {
                    "url": "https://example.com/image.jpg",
                    "alt": "Alt text for the image",
                    "description": "Description of the image",
                },
                "in_all_news": True,
                "is_liveblog": False,
                "is_highlight": False,
                "is_district": False,
                "creation_datetime": "2024-01-01T12:00:00Z",
                "publication_datetime": "2024-01-01T12:00:00Z",
                "expiration_datetime": None,
            },
            {
                "foreign_id": "123124",
                "title": "Working image article",
                "url": "https://example.com/test-article-2",
                "modification_datetime": "2024-01-01T12:00:00Z",
                "image": {
                    "url": "https://example.com/image-2.jpg",
                    "alt": "Alt text for the second image",
                    "description": "Description of the second image",
                },
                "in_all_news": True,
                "is_liveblog": False,
                "is_highlight": False,
                "is_district": False,
                "creation_datetime": "2024-01-01T12:00:00Z",
                "publication_datetime": "2024-01-01T12:00:00Z",
                "expiration_datetime": None,
            },
        ]
        mock_image_set_service.return_value.get_or_upload_from_url.side_effect = [
            ConnectionError("Upload timed out"),
            ConnectionError("Upload timed out"),
        ]

        loader = NewsArticleLoader(
            image_set_service=mock_image_set_service.return_value
        )

        loader.load(transformed_data)

        self.assertEqual(NewsArticle.objects.count(), 2)
        self.assertEqual(NewsArticleImage.objects.count(), 0)
        self.assertTrue(NewsArticle.objects.filter(foreign_id="123124").exists())
        self.assertFalse(
            NewsArticleImage.objects.filter(article__foreign_id="123124").exists()
        )

    def test_load_with_wrong_liveblog_messages(self):
        transformed_data = [
            {
                "foreign_id": "123125",
                "title": "Liveblog article",
                "url": "https://example.com/test-article-3",
                "modification_datetime": "2024-01-01T12:00:00Z",
                "in_all_news": True,
                "is_liveblog": True,
                "is_highlight": False,
                "is_district": False,
                "creation_datetime": "2024-01-01T12:00:00Z",
                "publication_datetime": "2024-01-01T12:00:00Z",
                "expiration_datetime": None,
                "liveblog_messages": "not a list",
            }
        ]

        loader = NewsArticleLoader(image_set_service=None)

        loader.load(transformed_data)
        self.assertTrue(NewsArticle.objects.filter(foreign_id="123125").exists())
        self.assertFalse(
            LiveBlogItem.objects.filter(article__foreign_id="123125").exists()
        )

    def test_get_news_article_object(self):
        article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "body": "A body",
            "summary": "A summary",
            "intro": "An intro",
            "in_all_news": True,
            "is_highlight": False,
            "is_liveblog": False,
            "is_district": False,
            "district": None,
            "url": "https://example.com/article/123123",
            "creation_datetime": "2024-01-01T12:00:00Z",
            "modification_datetime": "2024-01-01T12:00:00Z",
            "publication_datetime": "2024-01-01T12:00:00Z",
            "expiration_datetime": "2024-01-01T12:00:00Z",
            "image": {
                "url": "https://example.com/image.jpg",
                "alt": "Alt text for the image",
                "description": "Description of the image",
            },
        }
        news_article = self.loader._get_news_article_object(article_data)
        self.assertEqual(news_article.title, article_data["title"])
        self.assertEqual(news_article.url, article_data["url"])
        self.assertEqual(
            news_article.modification_datetime, article_data["modification_datetime"]
        )
        self.assertTrue(news_article.in_all_news)
        self.assertFalse(news_article.is_liveblog)

    def test_get_news_article_object_with_explicit_flags(self):
        article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "body": "A body",
            "in_all_news": True,
            "is_highlight": True,
            "is_liveblog": True,
            "is_district": True,
            "district": "noord",
            "url": "https://example.com/article/123123",
            "publication_datetime": "2024-01-01T12:00:00Z",
        }
        news_article = self.loader._get_news_article_object(article_data)

        self.assertTrue(news_article.in_all_news)
        self.assertTrue(news_article.is_highlight)
        self.assertTrue(news_article.is_liveblog)
        self.assertTrue(news_article.is_district)
        # body is None because the article is a liveblog, and liveblogs have liveblog items instead of a body
        self.assertIsNone(news_article.body)

    def test_upsert_news_articles(self):
        article = NewsArticle(
            foreign_id=123123,
            title="A title",
            body="A body",
            summary="A summary",
            intro="An intro",
            in_all_news=True,
            is_highlight=False,
            is_liveblog=False,
            is_district=False,
            district=None,
            url="https://example.com/article/123123",
            creation_datetime="2024-01-01T12:00:00Z",
            modification_datetime="2024-01-01T12:00:00Z",
            publication_datetime="2024-01-01T12:00:00Z",
            expiration_datetime="2024-01-01T12:00:00Z",
        )

        self.loader._upsert_news_articles([article])
        self.assertEqual(NewsArticle.objects.count(), 1)
        self.assertEqual(NewsArticle.objects.first().title, article.title)
        self.assertFalse(NewsArticle.objects.first().deleted)

    def test_upsert_news_articles_reactivates_deleted_article(self):
        existing_article = baker.make(
            NewsArticle,
            foreign_id=123123,
            deleted=True,
            in_all_news=True,
            is_highlight=False,
            is_liveblog=False,
            is_district=False,
            district=None,
            url="https://example.com/article/123123",
            title="Old title",
            modification_datetime="2024-01-01T12:00:00Z",
            publication_datetime="2024-01-01T12:00:00Z",
        )
        old_last_seen = timezone.now() - timezone.timedelta(hours=3)
        NewsArticle.objects.filter(id=existing_article.id).update(
            last_seen=old_last_seen
        )

        updated_article = self.loader._get_news_article_object(
            {
                "foreign_id": "123123",
                "title": "New title",
                "body": "A body",
                "summary": "A summary",
                "intro": "An intro",
                "in_all_news": True,
                "is_highlight": False,
                "is_liveblog": False,
                "is_district": False,
                "district": None,
                "url": "https://example.com/article/123123",
                "creation_datetime": "2024-01-01T12:00:00Z",
                "modification_datetime": "2024-01-01T13:00:00Z",
                "publication_datetime": "2024-01-01T13:00:00Z",
                "expiration_datetime": None,
            }
        )

        self.loader._upsert_news_articles([updated_article])

        existing_article.refresh_from_db()
        self.assertFalse(existing_article.deleted)
        self.assertEqual(existing_article.title, "New title")
        self.assertGreater(existing_article.last_seen, old_last_seen)

    def test_garbage_collect_unseen_articles_marks_only_stale_articles(self):
        stale_article = baker.make(NewsArticle, deleted=False, in_all_news=True)
        recent_article = baker.make(NewsArticle, deleted=False, in_all_news=True)
        cut_off_timestamp = timezone.now() - timezone.timedelta(minutes=45)

        NewsArticle.objects.filter(id=stale_article.id).update(
            last_seen=timezone.now() - timezone.timedelta(hours=3)
        )
        NewsArticle.objects.filter(id=recent_article.id).update(
            last_seen=timezone.now() - timezone.timedelta(minutes=30)
        )

        deleted_count = garbage_collect_unseen_articles(
            cut_off_timestamp=cut_off_timestamp
        )

        stale_article.refresh_from_db()
        recent_article.refresh_from_db()

        self.assertEqual(deleted_count, 1)
        self.assertTrue(stale_article.deleted)
        self.assertFalse(recent_article.deleted)

    def test_get_news_articles_dict(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T12:00:00Z",
        )
        articles_dict = self.loader._get_news_articles_dict()
        self.assertIn(str(article.foreign_id), articles_dict)
        self.assertEqual(articles_dict[str(article.foreign_id)].title, article.title)

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_article_images(self, mock_image_set_service):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T12:00:00Z",
        )
        article_data = {
            "foreign_id": "123123",
            "image": {
                "url": "https://example.com/image.jpg",
                "alt": "Alt text for the image",
                "description": "Description of the image",
            },
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 3)
        self.assertEqual(
            NewsArticleImage.objects.first().uri, "https://example.com/image.jpg"
        )

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_article_images_http_error(self, mock_image_set_service):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T12:00:00Z",
        )
        article_data = {
            "foreign_id": "123123",
            "image": {
                "url": "https://example.com/image.jpg",
                "alt": "Alt text for the image",
                "description": "Description of the image",
            },
        }

        mock_image_set_service.return_value.get_or_upload_from_url.side_effect = (
            HTTPError("Failed to fetch or upload image")
        )

        loader = NewsArticleLoader(
            image_set_service=mock_image_set_service.return_value
        )
        loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 0)

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_article_images_existing_remove(self, mock_image_set_service):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T12:00:00Z",
        )
        article_image = baker.make(
            NewsArticleImage,
            article=article,
            uri="https://example.com/other-image.jpg",
            width=123,
            height=456,
        )
        article_data = {
            "foreign_id": "123123",
            "image": {
                "url": "https://example.com/image.jpg",
                "alt": "Alt text for the image",
                "description": "Description of the image",
            },
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 3)
        self.assertEqual(
            NewsArticleImage.objects.first().uri, "https://example.com/image.jpg"
        )
        self.assertFalse(NewsArticleImage.objects.filter(id=article_image.id).exists())

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_article_images_existing_update(self, mock_image_set_service):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T12:00:00Z",
        )
        article_image = baker.make(
            NewsArticleImage,
            article=article,
            uri="https://example.com/image.jpg",
            width=10000,
            height=10000,
        )
        article_data = {
            "foreign_id": "123123",
            "image": {
                "url": "https://example.com/image.jpg",
                "alt": "Alt text for the image",
                "description": "Description of the image",
            },
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 3)
        self.assertEqual(
            NewsArticleImage.objects.first().uri, "https://example.com/image.jpg"
        )
        self.assertTrue(NewsArticleImage.objects.filter(id=article_image.id).exists())
        self.assertEqual(NewsArticleImage.objects.get(id=article_image.id).width, 123)

    def test_upsert_article_images_no_image(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            in_all_news=True,
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T12:00:00Z",
        )
        article_data = {
            "foreign_id": "123123",
        }

        self.loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 0)

    def test_upsert_liveblog_items_new(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            in_all_news=True,
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        liveblog_article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "modification_datetime": "2024-01-01T13:00:00Z",
            "is_liveblog": True,
            "liveblog_messages": [
                {
                    "title": "A liveblog item",
                    "creation_datetime": "2024-01-01T12:00:00Z",
                    "body": "Some body",
                },
                {
                    "title": "Another liveblog item",
                    "creation_datetime": "2024-01-01T13:00:00Z",
                    "body": "Some other body",
                },
            ],
        }
        self.loader._upsert_liveblog_items_and_item_images(
            liveblog_article_data, article
        )
        self.assertEqual(LiveBlogItem.objects.count(), 2)
        self.assertEqual(
            LiveBlogItem.objects.first().title,
            liveblog_article_data["liveblog_messages"][0]["title"],
        )

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_liveblog_item_images(self, mock_image_set_service):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        liveblog_item = baker.make(
            LiveBlogItem,
            article=article,
            title="A liveblog item",
            creation_datetime="2024-01-01T12:00:00Z",
        )
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)
        message = {
            "image": {
                "url": "https://example.com/image.jpg",
                "alt": "Alt text for the image",
                "description": "Description of the image",
            }
        }

        loader._upsert_liveblog_item_images(message, liveblog_item)

        mock_image_set_service.return_value.get_or_upload_from_url.assert_called_once_with(
            url=message["image"]["url"],
            description=message["image"]["alt"],
        )
        images = LiveBlogItemImage.objects.filter(liveblog_item=liveblog_item)
        self.assertEqual(images.count(), 3)
        self.assertEqual(set(images.values_list("foreign_id", flat=True)), {12345})
        self.assertEqual(
            set(images.values_list("alt", flat=True)), {"Alt text for the image"}
        )
        self.assertEqual(
            set(images.values_list("description", flat=True)),
            {"Description of the image"},
        )

    def test_upsert_liveblog_items_existing(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            in_all_news=True,
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        baker.make(
            LiveBlogItem,
            article=article,
            title="A liveblog item",
            body="With a body",
            creation_datetime="2024-01-01T12:00:00Z",
            message_order=0,
        )
        liveblog_article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "modification_datetime": "2024-01-01T13:00:00Z",
            "is_liveblog": True,
            "liveblog_messages": [
                {
                    "title": "Some title",
                    "creation_datetime": "2024-01-01T12:00:00Z",
                    "body": "Some body",
                },
                {
                    "title": "Another liveblog item",
                    "creation_datetime": "2024-01-01T13:00:00Z",
                    "body": "Some other body",
                },
            ],
        }
        self.loader._upsert_liveblog_items_and_item_images(
            liveblog_article_data, article
        )

        # number of liveblog items should still be 2 (the existing one should be updated, not duplicated, and the new one should be created)
        self.assertEqual(LiveBlogItem.objects.count(), 2)
        message_order_0_item = LiveBlogItem.objects.get(message_order=0)
        self.assertEqual(
            message_order_0_item.title,
            liveblog_article_data["liveblog_messages"][0]["title"],
        )

    def test_upsert_liveblog_items_creates_notifications_no_devices(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            in_all_news=True,
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        baker.make(
            LiveBlogItem,
            article=article,
            title="Existing liveblog item",
            body="With a body",
            creation_datetime="2024-01-01T12:00:00Z",
            message_order=0,
        )

        loader = NewsArticleLoader()
        liveblog_article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "modification_datetime": "2024-01-01T13:00:00Z",
            "is_liveblog": True,
            "liveblog_messages": [
                {
                    "title": "Updated existing item",
                    "creation_datetime": "2024-01-01T12:00:00Z",
                    "body": "Some body",
                },
                {
                    "title": "Brand new item",
                    "creation_datetime": "2024-01-01T13:00:00Z",
                    "body": "Some other body",
                },
            ],
        }

        loader._upsert_liveblog_items_and_item_images(liveblog_article_data, article)

        notifications = ScheduledNotification.objects.all()

        self.assertEqual(
            notifications.count(), 0
        )  # no notifications should be added when there are no devices

    def test_upsert_liveblog_items_creates_notifications_for_created_items_only(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            in_all_news=True,
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        baker.make(
            LiveBlogItem,
            article=article,
            title="Existing liveblog item",
            body="With a body",
            creation_datetime="2024-01-01T12:00:00Z",
            message_order=0,
        )
        baker.make(
            LiveblogNotification,
            article=article,
            device_id="device123",
        )

        loader = NewsArticleLoader()
        liveblog_article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "modification_datetime": "2024-01-01T13:00:00Z",
            "is_liveblog": True,
            "liveblog_messages": [
                {
                    "title": "Updated existing item",
                    "creation_datetime": "2024-01-01T12:00:00Z",
                    "body": "Some body",
                },
                {
                    "title": "Brand new item",
                    "creation_datetime": "2024-01-01T13:00:00Z",
                    "body": "Some other body",
                },
            ],
        }

        loader._upsert_liveblog_items_and_item_images(liveblog_article_data, article)

        notifications = ScheduledNotification.objects.all()

        self.assertEqual(
            notifications.count(), 1
        )  # one notification is added (for the new liveblog item)
        self.assertEqual(notifications[0].title, "Liveblog update")
        self.assertEqual(notifications[0].body, "Brand new item")

    @override_settings(ENABLE_LIVEBLOG_NOTIFICATIONS=False)
    def test_upsert_liveblog_items_skips_notifications_when_disabled(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            in_all_news=True,
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        baker.make(
            LiveBlogItem,
            article=article,
            title="Existing liveblog item",
            body="With a body",
            creation_datetime="2024-01-01T12:00:00Z",
            message_order=0,
        )
        baker.make(
            LiveblogNotification,
            article=article,
            device_id="device123",
        )

        loader = NewsArticleLoader()
        liveblog_article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "modification_datetime": "2024-01-01T13:00:00Z",
            "is_liveblog": True,
            "liveblog_messages": [
                {
                    "title": "Updated existing item",
                    "creation_datetime": "2024-01-01T12:00:00Z",
                    "body": "Some body",
                },
                {
                    "title": "Brand new item",
                    "creation_datetime": "2024-01-01T13:00:00Z",
                    "body": "Some other body",
                },
            ],
        }

        loader._upsert_liveblog_items_and_item_images(liveblog_article_data, article)

        self.assertEqual(LiveBlogItem.objects.count(), 2)
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_upsert_liveblog_items_no_notifications_for_updates(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
            in_all_news=True,
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        baker.make(
            LiveBlogItem,
            article=article,
            title="Existing liveblog item",
            body="With a body",
            creation_datetime="2024-01-01T12:00:00Z",
            message_order=0,
        )
        loader = NewsArticleLoader()
        liveblog_article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "modification_datetime": "2024-01-01T13:00:00Z",
            "is_liveblog": True,
            "liveblog_messages": [
                {
                    "title": "Updated existing item",
                    "creation_datetime": "2024-01-01T12:00:00Z",
                    "body": "Some body",
                },
            ],
        }

        loader._upsert_liveblog_items_and_item_images(liveblog_article_data, article)

        notifications = ScheduledNotification.objects.all()

        self.assertEqual(
            notifications.count(), 0
        )  # no notifications are added for updated liveblog items
