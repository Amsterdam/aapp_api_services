"""Modules models for MBS"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import ValidationError


class Module(models.Model):
    """Slug definitions with Status (Enum)"""

    class Status(models.IntegerChoices):
        """Enum for various statuses"""

        INACTIVE = 0, "inactive"
        ACTIVE = 1, "active"

    slug = models.CharField(max_length=100, blank=False, unique=True)
    status = models.IntegerField(
        blank=False, null=False, choices=Status.choices, default=Status.ACTIVE
    )


class ModuleVersion(models.Model):
    """Module version definition"""

    module = models.ForeignKey(Module, on_delete=models.PROTECT)
    version = models.CharField(max_length=100, blank=False, null=False)
    title = models.CharField(max_length=500, blank=False, null=False)
    icon = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=1000, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        """Constraints"""

        constraints = [
            models.UniqueConstraint(
                fields=["module", "version"], name="unique_module_version"
            )
        ]


class AppRelease(models.Model):
    version = models.CharField(max_length=100, blank=False, null=False, unique=True)
    release_notes = models.CharField(max_length=2000, blank=True, null=True)
    published = models.DateTimeField(null=True)
    unpublished = models.DateTimeField(null=True)
    deprecated = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    module_order = ArrayField(
        models.CharField(max_length=500, blank=False), blank=False
    )

    def save(self, *args, **kwargs):
        # Check if slug exists as Module
        for slug in self.module_order:
            module = Module.objects.filter(slug=slug).first()
            if module is None:
                raise ValidationError(
                    f"Given slug '{slug}' in module_order does not exist as Module"
                )

        # Check if slugs in module_order are unique
        if len(set(self.module_order)) != len(self.module_order):
            raise ValidationError("Slugs in module_order are not unique")

        return super().save(*args, **kwargs)


class ReleaseModuleStatus(models.Model):
    class Status(models.IntegerChoices):
        """Enum for various statuses"""

        INACTIVE = 0, "inactive"
        ACTIVE = 1, "active"

    app_release = models.ForeignKey(AppRelease, on_delete=models.CASCADE)
    module_version = models.ForeignKey(ModuleVersion, on_delete=models.CASCADE)
    status = models.IntegerField(
        blank=False, null=False, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:
        """Constraints"""

        constraints = [
            models.UniqueConstraint(
                fields=["app_release", "module_version"],
                name="unique_app_release_module_version",
            )
        ]
