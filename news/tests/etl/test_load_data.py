from unittest.mock import patch

from django.test import TestCase
from model_bakery import baker
from requests.exceptions import HTTPError

from news.etl.load_data import NewsArticleLoader
from news.models import LiveBlogItem, LiveBlogItemImage, NewsArticle, NewsArticleImage


class LoadDataTest(TestCase):
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
                "image_url": "https://example.com/image.jpg",
                "type": "article",
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
        self.assertEqual(NewsArticleImage.objects.count(), 3)

    def test_get_news_article_object(self):
        article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "body": "A body",
            "summary": "A summary",
            "intro": "An intro",
            "type": "article",
            "district": None,
            "url": "https://example.com/article/123123",
            "creation_datetime": "2024-01-01T12:00:00Z",
            "modification_datetime": "2024-01-01T12:00:00Z",
            "publication_datetime": "2024-01-01T12:00:00Z",
            "expiration_datetime": "2024-01-01T12:00:00Z",
            "image_url": "https://example.com/image.jpg",
        }
        news_article = self.loader._get_news_article_object(article_data)
        self.assertEqual(news_article.title, article_data["title"])
        self.assertEqual(news_article.url, article_data["url"])
        self.assertEqual(
            news_article.modification_datetime, article_data["modification_datetime"]
        )

    def test_upsert_news_articles(self):
        article = NewsArticle(
            foreign_id=123123,
            title="A title",
            body="A body",
            summary="A summary",
            intro="An intro",
            type="article",
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
            "image_url": "https://example.com/image.jpg",
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 3)
        self.assertEqual(
            NewsArticleImage.objects.first().url, "https://example.com/image.jpg"
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
            "image_url": "https://example.com/image.jpg",
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
            url="https://example.com/other-image.jpg",
            width=123,
            height=456,
        )
        article_data = {
            "foreign_id": "123123",
            "image_url": "https://example.com/source-image.jpg",
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 3)
        self.assertEqual(
            NewsArticleImage.objects.first().url, "https://example.com/image.jpg"
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
            url="https://example.com/image.jpg",
            width=10000,
            height=10000,
        )
        article_data = {
            "foreign_id": "123123",
            "image_url": "https://example.com/source-image.jpg",
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_article_images(article_data, article)
        self.assertEqual(NewsArticleImage.objects.count(), 3)
        self.assertEqual(
            NewsArticleImage.objects.first().url, "https://example.com/image.jpg"
        )
        self.assertTrue(NewsArticleImage.objects.filter(id=article_image.id).exists())
        self.assertEqual(NewsArticleImage.objects.get(id=article_image.id).width, 123)

    def test_upsert_article_images_no_image(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
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
            url="https://example.com/article/123123",
            modification_datetime="2024-01-01T13:00:00Z",
        )
        liveblog_article_data = {
            "foreign_id": "123123",
            "title": "A title",
            "modification_datetime": "2024-01-01T13:00:00Z",
            "type": "liveblog",
            "body": [
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
        self.loader._upsert_liveblog_items_and_liveblog_item_images(
            liveblog_article_data, article
        )
        self.assertEqual(LiveBlogItem.objects.count(), 2)
        self.assertEqual(
            LiveBlogItem.objects.first().title,
            liveblog_article_data["body"][0]["title"],
        )

    def test_upsert_liveblog_items_existing(self):
        article = baker.make(
            NewsArticle,
            foreign_id=123123,
            title="A title",
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
            "type": "liveblog",
            "body": [
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
        self.loader._upsert_liveblog_items_and_liveblog_item_images(
            liveblog_article_data, article
        )

        # number of liveblog items should still be 2 (the existing one should be updated, not duplicated, and the new one should be created)
        self.assertEqual(LiveBlogItem.objects.count(), 2)
        message_order_0_item = LiveBlogItem.objects.get(message_order=0)
        self.assertEqual(
            message_order_0_item.title,
            liveblog_article_data["body"][0]["title"],
        )

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_liveblog_item_images(self, mock_image_set_service):
        liveblog_item = baker.make(
            LiveBlogItem,
            title="A title",
            body="Some body",
            creation_datetime="2024-01-01T12:00:00Z",
        )
        message = {
            "image_url": "https://example.com/source-image.jpg",
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_liveblog_item_images(message, liveblog_item)
        self.assertEqual(LiveBlogItemImage.objects.count(), 3)
        self.assertEqual(
            LiveBlogItemImage.objects.first().url, "https://example.com/image.jpg"
        )

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_liveblog_item_images_http_error(self, mock_image_set_service):
        liveblog_item = baker.make(
            LiveBlogItem,
            title="A title",
            body="Some body",
            creation_datetime="2024-01-01T12:00:00Z",
        )
        message = {
            "image_url": "https://example.com/image.jpg",
        }

        mock_image_set_service.return_value.get_or_upload_from_url.side_effect = (
            HTTPError("Failed to fetch or upload image")
        )

        loader = NewsArticleLoader(
            image_set_service=mock_image_set_service.return_value
        )
        loader._upsert_liveblog_item_images(message, liveblog_item)
        self.assertEqual(LiveBlogItemImage.objects.count(), 0)

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_liveblog_item_images_existing_remove(self, mock_image_set_service):
        liveblog_item = baker.make(
            LiveBlogItem,
            title="A title",
            body="Some body",
            creation_datetime="2024-01-01T12:00:00Z",
        )
        liveblog_item_image = baker.make(
            LiveBlogItemImage,
            liveblog_item=liveblog_item,
            url="https://example.com/other-image.jpg",
            width=123,
            height=456,
        )
        message = {
            "image_url": "https://example.com/source-image.jpg",
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_liveblog_item_images(message, liveblog_item)
        self.assertEqual(LiveBlogItemImage.objects.count(), 3)
        self.assertEqual(
            LiveBlogItemImage.objects.first().url, "https://example.com/image.jpg"
        )
        self.assertFalse(
            LiveBlogItemImage.objects.filter(id=liveblog_item_image.id).exists()
        )

    @patch("news.etl.load_data.ImageSetService")
    def test_upsert_liveblog_item_images_existing_update(self, mock_image_set_service):
        liveblog_item = baker.make(
            LiveBlogItem,
            title="A title",
            body="Some body",
            creation_datetime="2024-01-01T12:00:00Z",
        )
        liveblog_item_image = baker.make(
            LiveBlogItemImage,
            liveblog_item=liveblog_item,
            url="https://example.com/image.jpg",
            width=10000,
            height=10000,
        )
        message = {
            "image_url": "https://example.com/source-image.jpg",
        }
        loader = self._set_mock_image_set_service_side_effect(mock_image_set_service)

        loader._upsert_liveblog_item_images(message, liveblog_item)
        self.assertEqual(LiveBlogItemImage.objects.count(), 3)
        self.assertEqual(
            LiveBlogItemImage.objects.first().url, "https://example.com/image.jpg"
        )
        self.assertTrue(
            LiveBlogItemImage.objects.filter(id=liveblog_item_image.id).exists()
        )
        self.assertEqual(
            LiveBlogItemImage.objects.get(id=liveblog_item_image.id).width, 123
        )

    def test_upsert_liveblog_item_images_no_image(self):
        liveblog_item = baker.make(
            LiveBlogItem,
            title="A title",
            body="Some body",
            creation_datetime="2024-01-01T12:00:00Z",
        )
        message = {}

        self.loader._upsert_liveblog_item_images(message, liveblog_item)
        self.assertEqual(LiveBlogItemImage.objects.count(), 0)
