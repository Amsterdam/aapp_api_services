from django.conf import settings
from django.db import IntegrityError, models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone

from construction_work.utils.model_utils import create_id_dict
from construction_work.validators import AmsterdamEmailValidator


class Project(models.Model):
    """Projects db model"""

    foreign_id = models.BigIntegerField(blank=False, unique=True, null=False)

    active = models.BooleanField(default=True, blank=True)
    last_seen = models.DateTimeField(blank=True, null=False)
    hidden = models.BooleanField(default=False, blank=True)

    title = models.CharField(
        max_length=1000, blank=True, null=True, default="", db_index=True
    )
    subtitle = models.CharField(max_length=1000, blank=True, null=True, db_index=True)
    coordinates = models.JSONField(blank=True, null=True, default=None)
    sections = models.JSONField(blank=True, null=True, default=dict)
    contacts = models.JSONField(blank=True, null=True, default=list)
    timeline = models.JSONField(blank=True, null=True, default=dict)
    image = models.JSONField(blank=True, null=True, default=dict)
    images = models.JSONField(blank=True, null=True, default=list)
    url = models.URLField(max_length=2048, blank=True, null=True)
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


class Article(models.Model):
    """Article db model"""

    foreign_id = models.BigIntegerField(blank=False, null=False, unique=True)

    active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    title = models.CharField(
        max_length=1000, blank=True, null=True, default="", db_index=True
    )
    intro = models.TextField(blank=True, null=True, default=None)
    body = models.TextField(blank=True, null=True, default=None)
    image = models.JSONField(blank=True, null=True, default=None)
    type = models.CharField(max_length=30, blank=True, null=True, default=None)
    projects = models.ManyToManyField(Project, blank=False)
    url = models.URLField(max_length=2048, blank=True, null=True)
    creation_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    modification_date = models.DateTimeField(
        default=timezone.now
    )  # If no date is provided use the current date
    publication_date = models.DateTimeField(default=None, null=True)
    expiration_date = models.DateTimeField(default=None, null=True)

    def get_id_dict(self):
        """Get id dict"""
        return create_id_dict(self)


class ProjectManager(models.Model):
    """Project manager db model"""

    name = models.CharField(max_length=1000, blank=False, null=False)
    email = models.EmailField(
        validators=[AmsterdamEmailValidator()], blank=False, null=False, unique=True
    )
    projects = models.ManyToManyField(Project, blank=True)


class Device(models.Model):
    """Mobile device running the mobile app"""

    device_id = models.CharField(max_length=200, blank=False, unique=True)
    firebase_token = models.CharField(max_length=1000, unique=True, null=True)
    os = models.CharField(max_length=7, blank=True, null=True, unique=False)
    followed_projects = models.ManyToManyField(Project, blank=True)
    last_access = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # The firebase_token field should be null
            # or not an empty unique string
            models.CheckConstraint(
                name="firebase_token_unique_or_null",
                check=models.Q(firebase_token__isnull=True)
                | ~models.Q(firebase_token=""),
            ),
        ]

    def save(self, *args, **kwargs):
        if (
            self.firebase_token is not None
            and self.__class__.objects.exclude(pk=self.pk)
            .filter(firebase_token=self.firebase_token)
            .exists()
        ):
            raise IntegrityError("The 'firebase_token' field must be unique or null.")
        super().save(*args, **kwargs)


class WarningMessage(models.Model):
    """Warning message db model"""

    title = models.CharField(max_length=1000, db_index=True)
    body = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    project_manager = models.ForeignKey(
        ProjectManager, blank=True, null=True, on_delete=models.SET_NULL
    )
    publication_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)
    author_email = models.EmailField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.author_email = settings.DEFAULT_WARNING_MESSAGE_EMAIL
        if self.project_manager is not None:
            self.author_email = self.project_manager.email

        super().save(*args, **kwargs)

    def get_id_dict(self):
        """Get id dict"""
        return create_id_dict(self)


class Image(models.Model):
    image = models.ImageField(upload_to="images/", null=True, blank=True)
    description = models.CharField(max_length=1000, blank=True, null=True, default=None)
    width = models.IntegerField()
    height = models.IntegerField()

    def save(self, *args, **kwargs):
        if not self.image:
            super().save(*args, **kwargs)

        self.width = self.image.width
        self.height = self.image.height

        super().save(*args, **kwargs)


class WarningImage(models.Model):
    """Warning image db model"""

    warning = models.ForeignKey(WarningMessage, on_delete=models.CASCADE, null=True)
    images = models.ManyToManyField(Image)


@receiver(pre_delete, sender=WarningImage)
def remove_images_for_warning_message(sender, instance, **kwargs):
    """Delete images for warning messages"""
    for image in instance.images.all():
        image.delete()


class Notification(models.Model):
    """Notifications db model"""

    title = models.CharField(max_length=1000, blank=False, null=False)
    body = models.TextField(blank=True, null=True)
    warning = models.ForeignKey(
        WarningMessage, on_delete=models.CASCADE, blank=False, null=False
    )
    publication_date = models.DateTimeField(auto_now_add=True, blank=True)
