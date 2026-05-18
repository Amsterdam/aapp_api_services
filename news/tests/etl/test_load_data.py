from unittest.mock import patch

from django.test import TestCase
from model_bakery import baker
from requests.exceptions import HTTPError

from news.etl.load_data import NewsArticleLoader
from news.models import NewsArticle, NewsArticleImage


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

    # def test_load(self):
    #     transformed_data = [
    #         {
    #             "foreign_id": "123123",
    #             "title": "Test Article",
    #             "url": "https://example.com/test-article",
    #             "modification_datetime": "2024-01-01T12:00:00Z",
    #             "image_url": "https://example.com/image.jpg",
    #             "type": "article",
    #             "creation_datetime": "2024-01-01T12:00:00Z",
    #             "publication_datetime": "2024-01-01T12:00:00Z",
    #             "expiration_datetime": None,
    #         }
    #     ]
    #     self._set_mock_image_set_service_side_effect(
    #         patch("news.etl.load_data.ImageSetService")
    #     )
    #     self.loader.load(transformed_data)
    #     self.assertEqual(NewsArticle.objects.count(), 1)
    #     self.assertEqual(
    #         NewsArticle.objects.first().title, transformed_data[0]["title"]
    #     )
    #     self.assertEqual(NewsArticleImage.objects.count(), 3)

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

    # @patch("news.etl.load_data.ImageSetService")
    # def test_gather_article_images(self, mock_image_set_service):
    #     transformed_data = [
    #         {
    #             "foreign_id": "123123",
    #             "type": "article",
    #             "body": "A body",
    #             "image_url": "https://example.com/image-test.jpg",
    #         }
    #     ]
    #     news_article = baker.make(
    #         NewsArticle,
    #         foreign_id=123123,
    #         title="Test Article",
    #         url="https://example.com/test-article",
    #         modification_datetime="2024-01-01T12:00:00Z",
    #     )
    #     news_articles_dict = {str(news_article.foreign_id): news_article}

    #     self._set_mock_image_set_service_side_effect(mock_image_set_service)

    #     loader = NewsArticleLoader(
    #         image_set_service=mock_image_set_service.return_value
    #     )
    #     article_images = loader._gather_article_images(
    #         transformed_data, news_articles_dict
    #     )
    #     self.assertEqual(len(article_images), 3)
    #     self.assertEqual(article_images[0].url, "https://example.com/image.jpg")

    # @patch("news.etl.load_data.ImageSetService")
    # def test_gather_liveblog_item_images(self, mock_image_set_service):
    #     transformed_data = [
    #         {
    #             "foreign_id": "123123",
    #             "type": "liveblog",
    #             "body": [
    #                 {
    #                     "title": "A liveblog message with image",
    #                     "body": "A liveblog message",
    #                     "creation_datetime": "2024-01-01T12:00:00Z",
    #                     "image_url": "https://example.com/example-image.jpg",
    #                 },
    #                 {
    #                     "title": "A liveblog message without image",
    #                     "body": "A liveblog message",
    #                     "creation_datetime": "2024-01-01T11:00:00Z",
    #                 },
    #             ],
    #         }
    #     ]
    #     news_article = baker.make(
    #         NewsArticle,
    #         foreign_id=123123,
    #         title="Test Article",
    #         url="https://example.com/test-article",
    #         modification_datetime="2024-01-01T12:00:00Z",
    #     )
    #     news_articles_dict = {str(news_article.foreign_id): news_article}

    #     self._set_mock_image_set_service_side_effect(mock_image_set_service)

    #     loader = NewsArticleLoader(
    #         image_set_service=mock_image_set_service.return_value
    #     )
    #     liveblog_item_images = (
    #         loader._create_liveblog_items_and_gather_liveblog_item_images(
    #             transformed_data, news_articles_dict
    #         )
    #     )
    #     self.assertEqual(len(liveblog_item_images), 3)
    #     self.assertEqual(
    #         LiveBlogItem.objects.count(), 2
    #     )  # Two liveblog items should be created in this test
    #     self.assertEqual(liveblog_item_images[0].url, "https://example.com/image.jpg")

    # @patch("news.etl.load_data.ImageSetService")
    # def test_gather_liveblog_item_images_http_error(self, mock_image_set_service):
    #     transformed_data = [
    #         {
    #             "foreign_id": "123123",
    #             "type": "liveblog",
    #             "body": [
    #                 {
    #                     "title": "A liveblog message with image",
    #                     "body": "A liveblog message",
    #                     "creation_datetime": "2024-01-01T12:00:00Z",
    #                     "image_url": "https://example.com/example-image.jpg",
    #                 },
    #                 {
    #                     "title": "A liveblog message without image",
    #                     "body": "A liveblog message",
    #                     "creation_datetime": "2024-01-01T11:00:00Z",
    #                 },
    #             ],
    #         }
    #     ]
    #     news_article = baker.make(
    #         NewsArticle,
    #         foreign_id=123123,
    #         title="Test Article",
    #         url="https://example.com/test-article",
    #         modification_datetime="2024-01-01T12:00:00Z",
    #     )
    #     news_articles_dict = {str(news_article.foreign_id): news_article}

    #     mock_image_set_service.return_value.get_or_upload_from_url.side_effect = (
    #         HTTPError("Failed to fetch or upload image")
    #     )

    #     loader = NewsArticleLoader(
    #         image_set_service=mock_image_set_service.return_value
    #     )
    #     liveblog_item_images = (
    #         loader._create_liveblog_items_and_gather_liveblog_item_images(
    #             transformed_data, news_articles_dict
    #         )
    #     )
    #     self.assertEqual(len(liveblog_item_images), 0)
    #     self.assertEqual(
    #         LiveBlogItem.objects.count(), 2
    #     )  # Two liveblog items should be created in this test

    # @patch("news.etl.load_data.ImageSetService")
    # def test_load_news_articles(self, mock_image_set_service):
    #     transformed_data = [
    #         {
    #             "foreign_id": "123123",
    #             "title": "Test Article",
    #             "url": "https://example.com/test-article",
    #             "modification_datetime": "2024-01-01T12:00:00Z",
    #             "image_url": "https://example.com/image.jpg",
    #             "type": "highlight",
    #             "creation_datetime": "2024-01-01T12:00:00Z",
    #             "publication_datetime": "2024-01-01T12:00:00Z",
    #             "expiration_datetime": None,
    #         },
    #         {
    #             "foreign_id": "1321235",
    #             "title": "Test Liveblog",
    #             "url": "https://example.com/test-article-2",
    #             "modification_datetime": "2024-01-02T12:00:00Z",
    #             "type": "article",
    #             # No image for this one
    #             "creation_datetime": "2024-01-02T12:00:00Z",
    #             "publication_datetime": "2024-01-02T12:00:00Z",
    #             "expiration_datetime": None,
    #         },
    #     ]

    #     self._set_mock_image_set_service_side_effect(mock_image_set_service)

    #     loader = NewsArticleLoader(
    #         image_set_service=mock_image_set_service.return_value
    #     )
    #     loader.load(transformed_data)
    #     self.assertEqual(NewsArticle.objects.count(), 2)
    #     self.assertEqual(
    #         NewsArticle.objects.first().title, transformed_data[0]["title"]
    #     )
    #     self.assertEqual(NewsArticle.objects.last().title, transformed_data[1]["title"])
    #     self.assertEqual(NewsArticleImage.objects.count(), 3)
