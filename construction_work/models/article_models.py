from django.db import models
from django.utils import timezone

from construction_work.models.project_models import BaseImage, BaseImageSource, Project
from construction_work.utils.model_utils import create_id_dict


class Article(models.Model):
    """Article db model"""

    foreign_id = models.BigIntegerField(unique=True)
    active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=1000, db_index=True)
    intro = models.TextField(blank=True, null=True, default=None)
    body = models.TextField(blank=True, null=True, default=None)
    type = models.CharField(max_length=30, blank=True, null=True, default=None)
    projects = models.ManyToManyField(Project)
    url = models.URLField(max_length=2048)
    creation_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    modification_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    publication_date = models.DateTimeField()
    expiration_date = models.DateTimeField(default=None, null=True)

    def get_id_dict(self):
        """Get id dict"""
        return create_id_dict(self)


class ArticleImage(BaseImage):
    parent = models.OneToOneField(
        Article, on_delete=models.CASCADE, related_name="image"
    )


class ArticleImageSource(BaseImageSource):
    image = models.ForeignKey(
        ArticleImage, on_delete=models.CASCADE, related_name="sources"
    )
