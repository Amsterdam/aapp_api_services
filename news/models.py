from django.db import models
from django.db.models import Q
from django.utils import timezone

ARTICLE_TYPE_CHOICES = [
    ("article", "Article"),
    ("highlight", "Highlight"),
    ("liveblog", "Liveblog"),
    ("district", "District"),
]

DISTRICT_TYPE_CHOICES = [
    ("noord", "Noord"),
    ("west", "West"),
    ("zuid", "Zuid"),
    ("oost", "Oost"),
    ("centrum", "Centrum"),
    ("nieuw-west", "Nieuw-West"),
    ("zuidoost", "Zuidoost"),
    ("weesp", "Weesp"),
]


class NewsArticleQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(deleted=False)


class VisibleNewsArticleManager(models.Manager):
    def get_queryset(self):
        return NewsArticleQuerySet(self.model, using=self._db).visible()


class NewsArticle(models.Model):
    """News Article db model"""

    objects = models.Manager()
    visible_objects = VisibleNewsArticleManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="district_article_requires_district",
                condition=(~Q(type="district") | Q(district__isnull=False)),
            ),
        ]

    foreign_id = models.BigIntegerField(unique=True)
    last_seen = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False, db_index=True)
    title = models.CharField(max_length=1000)
    summary = models.TextField(blank=True, null=True, default=None)
    intro = models.TextField(blank=True, null=True, default=None)
    body = models.TextField(blank=True, null=True, default=None)
    type = models.CharField(max_length=30, choices=ARTICLE_TYPE_CHOICES)
    in_all_news = models.BooleanField(default=False)
    is_highlight = models.BooleanField(default=False)
    is_liveblog = models.BooleanField(default=False)
    is_district = models.BooleanField(default=False)
    district = models.CharField(
        max_length=30,
        choices=DISTRICT_TYPE_CHOICES,
        blank=True,
        null=True,
        default=None,
    )
    url = models.URLField(max_length=2048)
    creation_datetime = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    modification_datetime = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    publication_datetime = models.DateTimeField()
    expiration_datetime = models.DateTimeField(default=None, null=True)
    is_active_liveblog = models.BooleanField(default=False)
    liveblog_notification_send = models.DateTimeField(default=None, null=True)
    liveblog_version = models.IntegerField(default=None, null=True)

    def __str__(self):
        return self.title


class LiveBlogItem(models.Model):
    article = models.ForeignKey(
        NewsArticle, on_delete=models.CASCADE, related_name="liveblog_items"
    )
    creation_datetime = models.DateTimeField()
    title = models.CharField(max_length=1000)
    body = models.TextField(blank=True, null=True)
    message_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["message_order"]


class BaseImage(models.Model):
    foreign_id = models.BigIntegerField(
        default=0
    )  # needs default value for migration, but will be set to the article's foreign_id when creating an image.
    uri = models.URLField(max_length=2048)
    width = models.IntegerField()
    height = models.IntegerField()

    class Meta:
        abstract = True


class NewsArticleImage(BaseImage):
    article = models.ForeignKey(
        NewsArticle, on_delete=models.CASCADE, related_name="images"
    )

    class Meta:
        unique_together = ("article", "uri")


class LiveBlogItemImage(BaseImage):
    liveblog_item = models.ForeignKey(
        LiveBlogItem, on_delete=models.CASCADE, related_name="images"
    )

    class Meta:
        unique_together = ("liveblog_item", "uri")


class LiveblogNotification(models.Model):
    class Meta:
        unique_together = ("article", "device_id")

    device_id = models.CharField(max_length=255)
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE)
