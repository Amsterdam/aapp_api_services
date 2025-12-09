from django.contrib.auth.models import User
from django.db import models
from django.db.models import ForeignKey


class NotificationSchedule(models.Model):
    """
    Model to store scheduled notifications.
    """

    device_id = models.CharField(max_length=255, primary_key=True)
    bag_nummeraanduiding_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)


class ManualNotification(models.Model):
    class Meta:
        verbose_name = "Notificatie"
        verbose_name_plural = "Notificaties"

    title = models.CharField("Titel", max_length=255)
    message = models.TextField("Bericht")
    created_by = ForeignKey(
        User,
        verbose_name="Aangemaakt door",
        on_delete=models.PROTECT,
        related_name="manual_notifications",
    )
    send_at = models.DateTimeField("Verstuurd op", null=True, blank=True)
    nr_sessions = models.PositiveIntegerField(
        "Aantal berichten verstuurd", default=0, editable=False
    )

    def __str__(self) -> str:
        return f"Notificatie: {self.title[:50]}"
