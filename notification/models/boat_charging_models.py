from django.db import models

from notification.models.notification_models import Device


class BoatChargingSession(models.Model):
    """
    Record to determine which device wants to receive burning guide notifications and
    for which address (postal_code).
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
