import logging
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from requests import HTTPError, RequestException

from core.services.image_set import ImageSetService
from news.models.article_models import (
    LiveBlogItem,
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


@dataclass(frozen=True)
class ArticleLoadResult:
    created_count: int


class NewsArticleLoader:
    """
    Loader class for ingesting news articles and liveblogs into the database.
    Handles upserts, image processing, and liveblog item management.
    """

    def __init__(
        self,
        *,
        image_set_service: ImageSetService | None = None,
        new_liveblog_notification_service: NewLiveblogNotificationService | None = None,
        liveblog_update_notification_service: LiveblogUpdateNotificationService
        | None = None,
    ):
        self.image_set_service = (
            image_set_service if image_set_service is not None else ImageSetService()
        )
        self.new_liveblog_notification_service = (
            new_liveblog_notification_service
            if new_liveblog_notification_service is not None
            else NewLiveblogNotificationService()
        )
        self.liveblog_update_notification_service = (
            liveblog_update_notification_service
            if liveblog_update_notification_service is not None
            else LiveblogUpdateNotificationService()
        )

    def load(self, transformed_data: list[dict]):
        """
        Load transformed news articles into the database.
        This method handles upserting articles based on their unique foreign_id.
        """
        logger.info(
            "Load news data into database.",
            extra={"article_count": len(transformed_data)},
        )
        incoming_foreign_ids = self._get_incoming_foreign_ids(transformed_data)
        existing_foreign_ids = self._get_existing_foreign_ids(incoming_foreign_ids)
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
                logger.error(
                    "Unable to load article images or liveblog items",
                    extra={"news_article_foreign_id": news_article.foreign_id},
                    exc_info=e,
                )

        return ArticleLoadResult(
            created_count=len(incoming_foreign_ids - existing_foreign_ids)
        )

    def _get_incoming_foreign_ids(self, transformed_data: list[dict]) -> set[int]:
        return {
            int(article_data["foreign_id"])
            for article_data in transformed_data
            if article_data.get("foreign_id") is not None
        }

    def _get_existing_foreign_ids(self, incoming_foreign_ids: set[int]) -> set[int]:
        if not incoming_foreign_ids:
            return set()

        return set(
            NewsArticle.objects.filter(foreign_id__in=incoming_foreign_ids).values_list(
                "foreign_id", flat=True
            )
        )

    def _get_news_article_object(self, data: dict) -> NewsArticle:
        """
        Convert a dictionary of news article data into a NewsArticle model instance.
        Handles the mapping of fields from the transformed data to the model fields.
        """

        return NewsArticle(
            foreign_id=data.get("foreign_id"),
            deleted=False,
            title=data.get("title"),
            body=data.get("body") if not data.get("is_liveblog", False) else None,
            summary=data.get("summary"),
            intro=data.get("intro"),
            in_all_news=data.get("in_all_news", False) or False,
            is_highlight=data.get("is_highlight", False) or False,
            is_liveblog=data.get("is_liveblog", False) or False,
            is_district=data.get("is_district", False) or False,
            is_construction_work=data.get("is_construction_work", False) or False,
            district=data.get("district"),
            url=data.get("url"),
            creation_datetime=data.get("creation_datetime"),
            modification_datetime=data.get("modification_datetime"),
            publication_datetime=data.get("publication_datetime"),
            expiration_datetime=data.get("expiration_datetime"),
            last_seen=timezone.now(),
            is_active_liveblog=data.get("is_active_liveblog", False) or False,
        )

    def _upsert_news_articles(self, news_articles_list: list[NewsArticle]) -> None:
        NewsArticle.objects.bulk_create(
            news_articles_list,
            update_conflicts=True,
            unique_fields=["foreign_id"],
            update_fields=[
                "deleted",
                "title",
                "body",
                "summary",
                "intro",
                "in_all_news",
                "is_highlight",
                "is_liveblog",
                "is_district",
                "is_construction_work",
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

        unsend_liveblogs = NewsArticle.objects.filter(
            is_liveblog=True,
            is_active_liveblog=True,
            liveblog_notification_send=None,
        )
        for liveblog in unsend_liveblogs:
            logger.info(f"New active liveblog with foreign_id {liveblog.foreign_id}")

            with transaction.atomic():
                if settings.ENABLE_LIVEBLOG_NOTIFICATIONS:
                    self.new_liveblog_notification_service.send(
                        liveblog_id=liveblog.id, liveblog_title=liveblog.title
                    )
                else:
                    logger.info(
                        "Liveblog notifications are disabled; suppressing new liveblog notification",
                        extra={"news_article_foreign_id": liveblog.foreign_id},
                    )

                # Make sure notifications will only be send once per liveblog
                liveblog.liveblog_notification_send = timezone.now()
                liveblog.save(update_fields=["liveblog_notification_send"])

    def _get_news_articles_dict(self) -> dict[str, NewsArticle]:
        news_article_objects = NewsArticle.objects.all()
        return {str(article.foreign_id): article for article in news_article_objects}

    def _upsert_article_images(self, article: dict, news_article: NewsArticle):
        image_set_data = self._get_image_set_data(article)
        if not image_set_data:
            return []

        image_sources = self._build_article_images(news_article, image_set_data)
        self._delete_removed_article_images(news_article, image_sources)
        self._upsert_article_image_sources(image_sources)
        return image_sources

    def _get_image_set_data(self, article: dict) -> dict | None:
        image_url = article.get("image_url")
        if not image_url:
            return None

        try:
            return self.image_set_service.get_or_upload_from_url(image_url)
        except (HTTPError, RequestException) as error:
            logger.error(
                "Error getting or uploading image",
                extra={
                    "image_url": image_url,
                    "news_article_foreign_id": article.get("foreign_id"),
                },
                exc_info=error,
            )
            return None

    def _build_article_images(
        self,
        news_article: NewsArticle,
        image_set_data: dict,
    ) -> list[NewsArticleImage]:
        return [
            NewsArticleImage(
                parent=news_article,
                foreign_id=image_set_data["id"],
                uri=variant["image"],
                width=variant["width"],
                height=variant["height"],
            )
            for variant in image_set_data.get("variants", [])
        ]

    def _delete_removed_article_images(
        self,
        news_article: NewsArticle,
        image_sources: list[NewsArticleImage],
    ):
        new_uris = {image.uri for image in image_sources}
        images_to_delete = NewsArticleImage.objects.filter(parent=news_article)
        if new_uris:
            images_to_delete = images_to_delete.exclude(uri__in=new_uris)

        if images_to_delete.exists():
            images_to_delete.delete()

    def _upsert_article_image_sources(
        self,
        image_sources: list[NewsArticleImage],
    ):
        if not image_sources:
            return

        NewsArticleImage.objects.bulk_create(
            image_sources,
            update_conflicts=True,
            unique_fields=["parent", "uri"],
            update_fields=["foreign_id", "width", "height"],
        )

    def _upsert_images_and_liveblog_items(
        self, article: dict, news_article: NewsArticle
    ):
        """
        Function to upsert the images (both article images and liveblog item images) and liveblog items for the transformed articles.

        We need the transformed data to still access the image urls and liveblog item data,
        and we need the news_articles_dict to associate the images and liveblog items with the correct NewsArticle instances in the database.
        """
        self._upsert_article_images(article, news_article)

        if article.get("is_liveblog", False):
            if not isinstance(article.get("body"), list):
                raise ArticleLoaderError(
                    "Something went wrong with importing the liveblog data"
                )

            self._upsert_liveblog_items(article, news_article)

    def _upsert_liveblog_items(self, article: dict, news_article: NewsArticle):
        messages = article.get("body")
        # make sure messages are sorted by creation_datetime ascending before creating LiveBlogItems
        messages.sort(key=lambda x: x.get("creation_datetime"))

        for i, message in enumerate(messages):
            _, created = LiveBlogItem.objects.update_or_create(
                article=news_article,
                message_order=i,
                defaults={
                    "creation_datetime": message.get("creation_datetime"),
                    "title": message.get("title"),
                    "body": message.get("body"),
                },
            )

            if created:
                self.send_liveblog_updates(message, news_article)

    def send_liveblog_updates(
        self,
        message,
        news_article: NewsArticle,
    ):
        if not settings.ENABLE_LIVEBLOG_NOTIFICATIONS:
            logger.info(
                "Liveblog notifications are disabled; suppressing liveblog update notification",
                extra={"news_article_foreign_id": news_article.foreign_id},
            )
            return

        device_ids = list(
            LiveblogNotification.objects.filter(article=news_article).values_list(
                "device_id", flat=True
            )
        )
        if device_ids:
            self.liveblog_update_notification_service.send(
                device_ids=device_ids,
                update_title=message.get("title"),
                liveblog_id=news_article.id,
            )


def garbage_collect_unseen_articles(*, threshold_seconds: int) -> int:
    stale_before = timezone.now() - timedelta(seconds=threshold_seconds)
    return NewsArticle.objects.filter(
        deleted=False,
        last_seen__lt=stale_before,
    ).update(deleted=True)
