from django.db import models
from django.utils import timezone

from construction_work.models.image_models import BaseImage
from construction_work.models.project_models import Project
from construction_work.utils.model_utils import create_id_dict


class Article(models.Model):
    """Article db model"""

    foreign_id = models.BigIntegerField(unique=True, null=True, blank=True)
    drupal_id = models.BigIntegerField(unique=True, null=True, blank=True)
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

    def deactivate(self, *args, **kwargs):
        """Deactivate & save"""
        self.active = False
        super(Article, self).save(*args, **kwargs)


class ArticleImage(BaseImage):
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="images"
    )

    class Meta:
        unique_together = ("article", "uri")
