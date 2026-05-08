from django.db import models
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


class NewsArticle(models.Model):
    """News Article db model"""

    foreign_id = models.BigIntegerField(unique=True)
    last_seen = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=1000)
    summary = models.TextField(blank=True, null=True, default=None)
    intro = models.TextField(blank=True, null=True, default=None)
    body = models.TextField(blank=True, null=True, default=None)
    type = models.CharField(max_length=30, choices=ARTICLE_TYPE_CHOICES)
    district = models.CharField(
        max_length=30,
        choices=DISTRICT_TYPE_CHOICES,
        blank=True,
        null=True,
        default=None,
    )
    url = models.URLField(max_length=2048)
    creation_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    modification_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    publication_date = models.DateTimeField()
    expiration_date = models.DateTimeField(default=None, null=True)

    def __str__(self):
        return self.title


class NewsArticleImage(models.Model):
    article = models.ForeignKey(
        NewsArticle, on_delete=models.CASCADE, related_name="images"
    )
    url = models.URLField(max_length=2048)
    width = models.IntegerField()
    height = models.IntegerField()

    def __str__(self):
        return f"{self.article.title} - {self.width}x{self.height}"
