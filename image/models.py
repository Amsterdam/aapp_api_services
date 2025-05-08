from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Index, Q, UniqueConstraint


class ImageVariant(models.Model):
    """
    Image model.
    - image: the actual image
    - width: width of the image in pixels
    - height: height of the image in pixels
    """

    image = models.ImageField(upload_to="image/")
    width = models.IntegerField()
    height = models.IntegerField()

    def save(self, *args, **kwargs):
        self.width = self.image.width
        self.height = self.image.height
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from Azure Storage before deleting the database record
        default_storage.delete(self.image.name)
        super().delete(*args, **kwargs)

    @property
    def image_url(self):
        # Construct the full URL dynamically. Otherwise, it will point directly to the Azure Blob Storage. The Blob Storage is not exposed to the public.
        return f"{settings.HOST}/media/{self.image}"


class ImageSet(models.Model):
    """
    Group of 3 image variants. One for each resolution.
    """

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["identifier"],
                condition=Q(identifier__isnull=False),
                name="image_imageset_unique_identifier",
            ),
        ]
        indexes = [
            Index(
                fields=["identifier"],
                condition=Q(identifier__isnull=False),
                name="idx_identifier_not_null",
            ),
        ]

    description = models.CharField(max_length=1000, blank=True, null=True)
    identifier = models.CharField(null=True)
    image_small = models.ForeignKey(
        ImageVariant, on_delete=models.CASCADE, related_name="small"
    )
    image_medium = models.ForeignKey(
        ImageVariant, on_delete=models.CASCADE, related_name="medium"
    )
    image_large = models.ForeignKey(
        ImageVariant, on_delete=models.CASCADE, related_name="large"
    )

    def delete(self, *args, **kwargs):
        self.image_small.delete()
        self.image_medium.delete()
        self.image_large.delete()
        super().delete(*args, **kwargs)
