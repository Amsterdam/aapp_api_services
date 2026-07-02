from django.db import models

from notification.models.notification_models import Device


class BoatChargingSession(models.Model):
    """
    Represents a boat-charging session associated with a device so we can track when
    boat-charging related notifications have been (or should be) sent for that session.
    """

    device = models.ForeignKey(
        Device,
        to_field="external_id",
        db_column="device_id",
        on_delete=models.CASCADE,
        related_name="boat_charging_session",
    )
    session_id = models.CharField(max_length=255)
    first_send_at = models.DateTimeField(null=True)
    second_send_at = models.DateTimeField(null=True)
    last_send_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
