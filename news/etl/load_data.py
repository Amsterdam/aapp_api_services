import logging

from django.db import transaction
from django.utils import timezone
from requests.exceptions import HTTPError

from core.services.image_set import ImageSetService
from news.models import (
    LiveBlogItem,
    LiveBlogItemImage,
    LiveblogNotification,
    NewsArticle,
    NewsArticleImage,
)
from news.services.notification import (
    LiveblogUpdateNotificationService,
    NewLiveblogNotificationService,
)

logger = logging.getLogger(__name__)


class ArticleLoaderError(Exception):
    pass


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

        news_articles_dict = self._get_news_articles_dict()  # {foreign_id: NewsArticle instance} for all articles in the database after upsert

        for article in transformed_data:
            news_article = news_articles_dict.get(str(article.get("foreign_id")))
            try:
                self._upsert_images_and_liveblog_items(article, news_article)
            except ArticleLoaderError as e:
                logger.error("Unable to load article images or liveblog items",
                             extra={"news_article_foreign_id": news_article.foreign_id}, exc_info=e)

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
            creation_datetime=data.get("creation_datetime"),
            modification_datetime=data.get("modification_datetime"),
            publication_datetime=data.get("publication_datetime"),
            expiration_datetime=data.get("expiration_datetime"),
            last_seen=timezone.now(),
            is_active_liveblog=data.get("is_active_liveblog") or False,
        )

    def _upsert_news_articles(self, news_articles_list: list[NewsArticle]):
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
                "creation_datetime",
                "modification_datetime",
                "publication_datetime",
                "expiration_datetime",
                "last_seen",
                "is_active_liveblog",
            ],
        )

        unsend_liveblogs = NewsArticle.objects.filter(type="liveblog", is_active_liveblog=True, liveblog_notification_send=None)
        for liveblog in unsend_liveblogs:
            logger.info(f"New active liveblog with foreign_id {liveblog.foreign_id}")

            with transaction.atomic():
                notification_service = NewLiveblogNotificationService()
                notification_service.send(liveblog_id=liveblog.id, liveblog_title=liveblog.title)

                # Make sure notifications will only be send once per liveblog
                liveblog.liveblog_notification_send = timezone.now()
                liveblog.save(update_fields=["liveblog_notification_send"])

    def _get_news_articles_dict(self) -> dict[str, NewsArticle]:
        news_article_objects = NewsArticle.objects.all()
        return {str(article.foreign_id): article for article in news_article_objects}

    def _upsert_images_and_liveblog_items(
        self, article: dict, news_article: NewsArticle
    ):
        """
        Function to upsert the images (both article images and liveblog item images) and liveblog items for the transformed articles.

        We need the transformed data to still access the image urls and liveblog item data,
        and we need the news_articles_dict to associate the images and liveblog items with the correct NewsArticle instances in the database.
        """
        self._upsert_article_images(article, news_article)

        if article.get("type") == "liveblog":
            if not isinstance(article.get("body"), list):
                raise ArticleLoaderError("Something went wrong with importing the liveblog data")

            self._upsert_liveblog_items_and_liveblog_item_images(article, news_article)

    def _upsert_article_images(self, article: dict, news_article: NewsArticle):
        """
        Upsert article images for a given article. If the article has an image_url, we will attempt to get or upload the image using the ImageSetService.
        Then we will upsert the NewsArticleImage instances for the article based on the image variants returned by the ImageSetService.
        The logic is as follows:
        - If an image with the same url already exists for the article, update its width and height
        - If there is an image for an article, but the url is different than the existing one, delete the old image and create a new one
        - If there is no image for an article, create a new one
        """
        image_url = article.get("image_url")
        if image_url:
            try:
                image_set_data = self.image_set_service.get_or_upload_from_url(
                    image_url
                )
            except HTTPError as e:
                logger.error(
                    "Error getting or uploading image",
                    extra={"image_url": image_url, "error": str(e)},
                )
                return

            # upsert article images
            image_sources = [
                NewsArticleImage(
                    article=news_article,
                    foreign_id=image_set_data[
                        "id"
                    ],  # use the image set id as the image foreign_id for reference.
                    url=v["image"],
                    width=v["width"],
                    height=v["height"],
                )
                for v in image_set_data["variants"]
            ]
            # Gather all URLs for this article from the new image_sources
            new_urls = {img.url for img in image_sources}
            # Find all existing images for this article
            existing_images = NewsArticleImage.objects.filter(article=news_article)
            # Delete images for this article whose URL is not in the new set
            images_to_delete = existing_images.exclude(url__in=new_urls)
            if images_to_delete.exists():
                images_to_delete.delete()

            # Upsert new images (create or update width/height)
            NewsArticleImage.objects.bulk_create(
                image_sources,
                update_conflicts=True,
                unique_fields=["article", "url"],
                update_fields=["width", "height"],
            )

    def _upsert_liveblog_items_and_liveblog_item_images(
        self, article: dict, news_article: NewsArticle
    ):
        messages = article.get("body")
        # make sure messages are sorted by creation_datetime ascending before creating LiveBlogItems
        messages.sort(key=lambda x: x.get("creation_datetime"))

        for i, message in enumerate(messages):
            liveblog_item, created = LiveBlogItem.objects.update_or_create(
                article=news_article,
                message_order=i,
                defaults={
                    "creation_datetime": message.get("creation_datetime"),
                    "title": message.get("title"),
                    "body": message.get("body"),
                },
            )

            image_set_id = self._upsert_liveblog_item_images(message, liveblog_item)
            if created:
                self.send_liveblog_updates(image_set_id, liveblog_item, message, news_article)

    def send_liveblog_updates(self, image_set_id: int | None, liveblog_item, message, news_article: NewsArticle):
        device_ids = list(
            LiveblogNotification.objects.filter(
                article=news_article
            ).values_list("device_id", flat=True)
        )
        if device_ids:
            update_notification_service = LiveblogUpdateNotificationService(
                use_image_service=True
            )
            update_notification_service.send(
                device_ids=device_ids,
                update_title=message.get("title"),
                liveblog_item_id=liveblog_item.id,
                image_set_id=image_set_id,
            )

    def _upsert_liveblog_item_images(
        self, message: dict, liveblog_item: LiveBlogItem
    ) -> int | None:
        """
        Upsert liveblog item images for a given liveblog item. If the liveblog item has an image_url, we will attempt to get or upload the image using the ImageSetService.
        Then we will upsert the LiveBlogItemImage instances for the liveblog item based on the image variants returned by the ImageSetService.
        The logic is as follows:
        - If an image with the same url already exists for the liveblog item, update its width and height
        - If there is an image for a liveblog item, but the url is different than the existing one, delete the old image and create a new one
        - If there is no image for a liveblog item, create a new one
        """
        image_url = message.get("image_url")
        if image_url:
            try:
                image_set_data = self.image_set_service.get_or_upload_from_url(
                    image_url
                )
            except HTTPError as e:
                logger.error(
                    "Error getting or uploading image",
                    extra={"image_url": image_url, "error": str(e)},
                )
                return
            image_set_id = image_set_data["id"]
            image_sources = [
                LiveBlogItemImage(
                    liveblog_item=liveblog_item,
                    foreign_id=image_set_id,  # use the image set id as the image foreign_id for reference.
                    url=v["image"],
                    width=v["width"],
                    height=v["height"],
                )
                for v in image_set_data["variants"]
            ]

            # Gather all URLs for this liveblog item from the new image_sources
            new_urls = {img.url for img in image_sources}
            # Find all existing images for this liveblog item
            existing_images = LiveBlogItemImage.objects.filter(
                liveblog_item=liveblog_item
            )
            # Delete images for this liveblog item whose URL is not in the new set
            images_to_delete = existing_images.exclude(url__in=new_urls)
            if images_to_delete.exists():
                images_to_delete.delete()

            # Upsert new images (create or update width/height)
            LiveBlogItemImage.objects.bulk_create(
                image_sources,
                update_conflicts=True,
                unique_fields=["liveblog_item", "url"],
                update_fields=["width", "height"],
            )

            return image_set_id
