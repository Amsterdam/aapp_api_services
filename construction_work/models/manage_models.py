from django.conf import settings
from django.db import IntegrityError, models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from construction_work.models.project_models import Project
from construction_work.utils.model_utils import create_id_dict
from construction_work.validators import AmsterdamEmailValidator


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
    notification_sent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.author_email = settings.DEFAULT_WARNING_MESSAGE_EMAIL
        if self.project_manager is not None:
            self.author_email = self.project_manager.email

        super().save(*args, **kwargs)

    def get_id_dict(self):
        """Get id dict"""
        return create_id_dict(self)


class Image(models.Model):
    image = models.ImageField(
        upload_to="construction-work/images/", null=True, blank=True
    )
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
