from django.db import models


class BurningGuideNotification(models.Model):
    """
    Model to store scheduled notifications.
    """

    device_id = models.CharField(max_length=255, primary_key=True)
    postal_code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    send_at = models.DateTimeField(null=True)
