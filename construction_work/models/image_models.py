from django.db import models


class BaseImage(models.Model):
    id = models.IntegerField(primary_key=True)
    alternativeText = models.CharField(null=True, blank=True)
    image_set = models.IntegerField()

    class Meta:
        abstract = True


class BaseImageSource(models.Model):
    uri = models.CharField()
    width = models.IntegerField()
    height = models.IntegerField()

    class Meta:
        abstract = True
