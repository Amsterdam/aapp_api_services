import uuid

from django.db import models
from django.utils import timezone


class Project(models.Model):
    """Projects db model"""

    foreign_id = models.BigIntegerField(unique=True)
    active = models.BooleanField(default=True)
    last_seen = models.DateTimeField()
    hidden = models.BooleanField(default=False)
    title = models.CharField(max_length=1000, db_index=True)
    subtitle = models.CharField(max_length=1000, blank=True, null=True)
    url = models.URLField(max_length=2048)
    timeline_title = models.CharField(max_length=1000, blank=True, null=True)
    timeline_intro = models.CharField(max_length=1000, blank=True, null=True)
    coordinates_lat = models.FloatField(blank=True, null=True)
    coordinates_lon = models.FloatField(blank=True, null=True)
    creation_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    modification_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    publication_date = models.DateTimeField(default=None, null=True)
    expiration_date = models.DateTimeField(default=None, null=True)

    class Meta:
        ordering = ["title"]

    def save(self, update_active=True, *args, **kwargs):
        if update_active:
            self.active = True
            self.last_seen = timezone.now()
        super(Project, self).save(*args, **kwargs)

    def deactivate(self, *args, **kwargs):
        """Deactivate & save"""
        self.active = False
        super(Project, self).save(*args, **kwargs)


class ProjectTimelineItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(null=True, blank=True)
    body = models.CharField(null=True, blank=True)
    collapsed = models.BooleanField(null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="items"
    )  # Recursive relationship
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="timeline_items",
    )


class BaseImage(models.Model):
    id = models.IntegerField(primary_key=True)
    aspectRatio = models.FloatField()
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


class ProjectImage(BaseImage):
    parent = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="image"
    )


class ProjectImageSource(BaseImageSource):
    image = models.ForeignKey(
        ProjectImage, on_delete=models.CASCADE, related_name="sources"
    )


class ProjectSection(models.Model):
    body = models.CharField(null=True, blank=True)
    title = models.CharField()
    type = models.CharField(
        max_length=10,
        choices=[
            (choice, choice) for choice in ["where", "what", "when", "work", "contact"]
        ],
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="sections"
    )


class ProjectSectionUrl(models.Model):
    url = models.CharField()
    label = models.CharField()
    section = models.ForeignKey(
        ProjectSection, on_delete=models.CASCADE, related_name="links"
    )


class ProjectContact(models.Model):
    id = models.FloatField(primary_key=True)
    name = models.CharField(null=True, blank=True)
    email = models.CharField(null=True, blank=True)
    phone = models.CharField(null=True, blank=True)
    position = models.CharField(null=True, blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="contacts"
    )
