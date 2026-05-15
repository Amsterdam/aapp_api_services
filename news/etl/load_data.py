import logging

from django.db import transaction
from django.utils import timezone
from requests.exceptions import HTTPError

from core.services.image_set import ImageSetService
from news.models import LiveBlogItem, LiveBlogItemImage, NewsArticle, NewsArticleImage

logger = logging.getLogger(__name__)


class NewsArticleLoader:
    """
    Loader class for ingesting news articles and liveblogs into the database.
    Handles upserts, image processing, and liveblog item management.
    """

    def __init__(self, image_set_service=None):
        self.image_set_service = image_set_service or ImageSetService()

    def load(self, transformed_data: list[dict]):
        """
        Load transformed news articles into the database.
        This method handles upserting articles based on their unique foreign_id.
        """
        news_articles_list = [
            self._get_news_article_object(data) for data in transformed_data
        ]
        self._upsert_news_articles(news_articles_list)

        news_articles_dict = self._get_news_articles_dict()

        all_article_images = self._gather_article_images(
            transformed_data, news_articles_dict
        )
        self._replace_article_images(all_article_images)

        self._delete_all_liveblog_items()
        all_liveblog_item_images = (
            self._create_liveblog_items_and_gather_liveblog_item_images(
                transformed_data, news_articles_dict
            )
        )
        self._replace_liveblog_item_images(all_liveblog_item_images)

    def _get_news_article_object(self, data: dict) -> NewsArticle:
        """
        Convert a dictionary of news article data into a NewsArticle model instance.
        Handles the mapping of fields from the transformed data to the model fields.
        """
        return NewsArticle(
            foreign_id=data.get("foreign_id"),
            title=data.get("title"),
            body=data.get("body") if data.get("type") != "liveblog" else None,
            summary=data.get("summary"),
            intro=data.get("intro"),
            type=data.get("type"),
            district=data.get("district"),
            url=data.get("url"),
            creation_date=data.get("creation_date"),
            modification_date=data.get("modification_date"),
            publication_date=data.get("publication_date"),
            expiration_date=data.get("expiration_date"),
            last_seen=timezone.now(),
        )

    def _upsert_news_articles(self, news_articles_list: list[NewsArticle]):
        with transaction.atomic():
            NewsArticle.objects.bulk_create(
                news_articles_list,
                update_conflicts=True,
                unique_fields=["foreign_id"],
                update_fields=[
                    "title",
                    "body",
                    "summary",
                    "intro",
                    "type",
                    "district",
                    "url",
                    "creation_date",
                    "modification_date",
                    "publication_date",
                    "expiration_date",
                    "last_seen",
                ],
            )

    def _get_news_articles_dict(self) -> dict[int, NewsArticle]:
        news_article_objects = NewsArticle.objects.all()
        return {article.foreign_id: article for article in news_article_objects}

    def _delete_all_liveblog_items(self):
        with transaction.atomic():
            LiveBlogItem.objects.all().delete()

    def _gather_article_images(
        self, transformed_data: list[dict], news_articles_dict: dict[int, NewsArticle]
    ) -> list[NewsArticleImage]:
        all_article_images = []
        for article in transformed_data:
            news_article = news_articles_dict.get(article.get("foreign_id"))
            if article.get("image_url") is not None:
                try:
                    image_set_data = self.image_set_service.get_or_upload_from_url(
                        article.get("image_url")
                    )
                except HTTPError as e:
                    logger.error(f"Error getting or uploading image: {e}")
                    continue
                image_sources = [
                    NewsArticleImage(
                        article=news_article,
                        url=v["image"],
                        width=v["width"],
                        height=v["height"],
                    )
                    for v in image_set_data["variants"]
                ]
                all_article_images.extend(image_sources)
        return all_article_images

    def _create_liveblog_items_and_gather_liveblog_item_images(
        self, transformed_data: list[dict], news_articles_dict: dict[int, NewsArticle]
    ) -> list[LiveBlogItemImage]:
        all_liveblog_item_images = []
        for article in transformed_data:
            news_article = news_articles_dict.get(article.get("foreign_id"))
            if article.get("type") == "liveblog" and isinstance(
                article.get("body"), list
            ):
                for message in article.get("body"):
                    liveblog_item = LiveBlogItem.objects.create(
                        article=news_article,
                        datetime=message.get("datetime"),
                        title=message.get("title"),
                        body=message.get("body"),
                    )
                    if message.get("image_url") is not None:
                        try:
                            image_set_data = (
                                self.image_set_service.get_or_upload_from_url(
                                    message.get("image_url")
                                )
                            )
                        except HTTPError as e:
                            logger.error(f"Error getting or uploading image: {e}")
                            continue
                        image_sources = [
                            LiveBlogItemImage(
                                liveblogitem=liveblog_item,
                                url=v["image"],
                                width=v["width"],
                                height=v["height"],
                            )
                            for v in image_set_data["variants"]
                        ]
                        all_liveblog_item_images.extend(image_sources)
        return all_liveblog_item_images

    def _replace_article_images(self, all_article_images: list[NewsArticleImage]):
        with transaction.atomic():
            NewsArticleImage.objects.all().delete()
            if all_article_images:
                NewsArticleImage.objects.bulk_create(all_article_images)

    def _replace_liveblog_item_images(
        self, all_liveblog_item_images: list[LiveBlogItemImage]
    ):
        with transaction.atomic():
            LiveBlogItemImage.objects.all().delete()
            if all_liveblog_item_images:
                LiveBlogItemImage.objects.bulk_create(all_liveblog_item_images)
