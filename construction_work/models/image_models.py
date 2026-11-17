from django.db import models


class BaseImage(models.Model):
    alternativeText = models.CharField(null=True, blank=True)
    image_set = (
        models.IntegerField()
    )  # id of the image set (from internal image service)
    foreign_id = models.IntegerField(null=True, blank=True)  # id of Drupal image

    class Meta:
        abstract = True


class BaseImageSource(models.Model):
    uri = models.CharField()
    width = models.IntegerField()
    height = models.IntegerField()

    class Meta:
        abstract = True
