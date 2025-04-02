from django.db import models


class NotificationSchedule(models.Model):
    """
    Model to store scheduled notifications.
    """

    device_id = models.CharField(max_length=255, primary_key=True)
    bag_nummeraanduiding_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
