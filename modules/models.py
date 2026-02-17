"""Modules models for MBS"""

import re

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import ForeignKey
from django.forms import ValidationError

from core.validators import AappDeeplinkValidator
from modules.icons import ModuleIconPath


class Module(models.Model):
    """Slug definitions with Status (Enum)"""

    class Status(models.IntegerChoices):
        """Enum for various statuses"""

        INACTIVE = 0, "inactive"
        ACTIVE = 1, "active"

    slug = models.CharField(max_length=100, unique=True)
    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)
    note = models.CharField(
        "Notitie",
        max_length=500,
        blank=True,
        null=True,
        help_text="Rede voor status wijziging. Alleen intern zichtbaar.",
    )
    app_reason = models.CharField(
        "App reden",
        max_length=500,
        blank=True,
        null=True,
        help_text="Rede voor status wijziging. Zichtbaar in de app.",
    )
    fallback_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL om als backup te gebruiken.",
    )
    button_label = models.CharField(
        "Knop label",
        max_length=150,
        default="Bekijk op Amsterdam.nl",
        help_text="Label voor de knop die naar de fallback URL verwijst.",
    )

    def __str__(self):
        return f"{self.slug} ({self.get_status_display()})"

    def clean(self):
        super().clean()

        if self.status == Module.Status.INACTIVE and not self.app_reason:
            raise ValidationError(
                "Een inactieve module moet een 'app reden' gedefinieerd hebben."
            )

        if self.status == Module.Status.ACTIVE:
            self.fallback_url = None
            self.app_reason = None
            self.note = None


class ModuleVersion(models.Model):
    """Module version definition"""

    module = models.ForeignKey(Module, on_delete=models.PROTECT)
    version = models.CharField("Versie", max_length=100)
    title = models.CharField("Titel", max_length=500)
    icon = models.CharField(
        "Icoon", max_length=100, choices=((i, i) for i in ModuleIconPath.keys())
    )
    description = models.TextField("Omschrijving", max_length=1000)
    created = models.DateTimeField("Aangemaakt", auto_now_add=True)
    modified = models.DateTimeField("Laatste wijziging", auto_now=True)

    class Meta:
        """Constraints"""

        constraints = [
            models.UniqueConstraint(
                fields=["module", "version"], name="unique_module_version"
            )
        ]

    def clean(self):
        # check is version is semantic versioning like "1.0.0"
        if not re.match(r"^\d+\.\d+\.\d+$", self.version):
            raise ValidationError(
                f"Versie '{self.version}' is geen semantic versioning format."
            )

    def __str__(self):
        return f"{self.title} ({self.version})"


class AppRelease(models.Model):
    version = models.CharField("Versie", max_length=100, unique=True)
    release_notes = models.CharField(max_length=2000, blank=True)
    published = models.DateTimeField(
        "Gepubliceerd",
        null=True,
        blank=True,
        help_text="De publicatiedatum bepaalt vanaf wanneer de release niet meer als pre-release te zien is en de release in aanmerking komt voor voor gebruik als latest version in update meldingen.",
    )
    unpublished = models.DateTimeField(
        "Ongepubliceerd",
        null=True,
        blank=True,
        help_text="De ongepubliceerd datum bepaalt vanaf wanneer gebruikers van deze release een geforceerde update melding krijgen en de app voor deze gebruikers onbruikbaar is.",
    )
    deprecated = models.DateTimeField(
        "Deprecated",
        null=True,
        blank=True,
        help_text="De deprecateddatum bepaalt vanaf wanneer gebruikers van deze release een update suggestie melding krijgen.",
    )
    created = models.DateTimeField("Aangemaakt", auto_now_add=True)
    modified = models.DateTimeField("Laatste bewerking", auto_now=True)
    modules = models.ManyToManyField(
        ModuleVersion,
        through="ReleaseModuleStatus",
        through_fields=("app_release", "module_version"),
        verbose_name="Modules in deze release",
    )
    module_order = ArrayField(
        models.CharField(max_length=500, blank=False),
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Release {self.version} ({self.created.date()})"


class ReleaseModuleStatus(models.Model):
    class Meta:
        """Constraints"""

        constraints = [
            models.UniqueConstraint(
                fields=["app_release", "module_version"],
                name="unique_app_release_module_version",
            )
        ]
        verbose_name = "Release Module State"
        verbose_name_plural = "Release Module Status"
        ordering = ["sort_order"]

    class Status(models.IntegerChoices):
        """Enum for various statuses"""

        INACTIVE = 0, "inactive"
        ACTIVE = 1, "active"

    app_release = models.ForeignKey(AppRelease, on_delete=models.PROTECT)
    module_version = models.ForeignKey(
        ModuleVersion, on_delete=models.PROTECT, verbose_name="Module versie"
    )
    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)
    sort_order = models.PositiveIntegerField(db_index=True)
    note = models.CharField(
        "Notitie",
        max_length=500,
        blank=True,
        null=True,
    )
    app_reason = models.CharField(
        "App reden",
        max_length=500,
        blank=True,
        null=True,
    )
    fallback_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )
    button_label = models.CharField(
        "Knop label",
        max_length=150,
        default="Bekijk op Amsterdam.nl",
        help_text="Label voor de knop die naar de fallback URL verwijst.",
    )

    def __str__(self):
        return ""

    def clean(self):
        super().clean()

        dup_exists = (
            ReleaseModuleStatus.objects.filter(
                app_release_id=self.app_release_id,
                module_version__module_id=self.module_version.module_id,
            )
            .exclude(pk=self.pk)
            .exists()
        )

        if dup_exists:
            raise ValidationError("Deze module bestaat al in de release.")

        if self.status == ReleaseModuleStatus.Status.INACTIVE and not self.app_reason:
            raise ValidationError(
                "In inactieve module moet een 'app reden' gedefinieerd hebben."
            )

        if self.status == ReleaseModuleStatus.Status.ACTIVE:
            self.fallback_url = None
            self.app_reason = None
            self.note = None

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.full_clean()
            super().save(*args, **kwargs)


class Notification(models.Model):
    class Meta:
        verbose_name = "Notificatie"
        verbose_name_plural = "Notificaties"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(url__isnull=True) | models.Q(deeplink__isnull=True)
                ),
                name="url_and_deeplink_mutually_exclusive",
            )
        ]

    title = models.CharField("Titel", max_length=255)
    message = models.TextField("Bericht")
    url = models.URLField(null=True, blank=True)
    deeplink = models.CharField(
        null=True, blank=True, validators=[AappDeeplinkValidator()]
    )
    created_by = ForeignKey(
        User,
        verbose_name="Aangemaakt door",
        on_delete=models.PROTECT,
        related_name="notifications",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    send_at = models.DateTimeField("Versturen op", null=True, blank=True)
    nr_sessions = models.PositiveIntegerField("Bereik", default=0, editable=False)
    is_test = models.BooleanField("Test notificatie", default=True)

    def __str__(self) -> str:
        return f"Notificatie: {self.title[:50]}"


class TestDevice(models.Model):
    class Meta:
        verbose_name = "Test toestel"
        verbose_name_plural = "Test toestellen"

    device_id = models.CharField("Device ID", max_length=255, unique=True)
    name = models.CharField("Naam", max_length=255, blank=True, null=True)
