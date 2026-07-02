from django.db import models

from notification.models.notification_models import Device


class WasteDevice(models.Model):
    """
    Record to determine which device wants to receive waste notifications and
    for which address (bag_nummeraanduiding_id).

    Note: updated_at is not used to keep track of when a user updates their bag_nummeraanduiding_id,
    but to determine if the scheduled notification should be sent (again).
    """

    device = models.OneToOneField(
        Device,
        to_field="external_id",
        db_column="device_id",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="waste_device",
    )
    bag_nummeraanduiding_id = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
