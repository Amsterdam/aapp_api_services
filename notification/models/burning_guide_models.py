from django.db import models

from notification.models.notification_models import Device


class BurningGuideDevice(models.Model):
    """
    Record to determine which device wants to receive burning guide notifications and
    for which address (postal_code).
    """

    device = models.OneToOneField(
        Device,
        to_field="external_id",
        db_column="device_id",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="burning_guide_device",
    )
    postal_code = models.CharField(max_length=4, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    send_at = models.DateTimeField(null=True)
