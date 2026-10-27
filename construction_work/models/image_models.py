from django.db import models


class BaseImage(models.Model):
    foreign_id = models.BigIntegerField()  # Image service image-set ID.
    uri = models.URLField(max_length=2048)
    width = models.IntegerField()
    height = models.IntegerField()

    class Meta:
        abstract = True
