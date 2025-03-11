import uuid

from django.db import models

from core.enums import Service


class Device(models.Model):
    """
    Entity that is open to receive push notifications.
    - external_id: provided by the device, e.g. a (hashed) device id
    - os: operating system of the device, e.g. 'android', 'ios'
    - firebase_token: provided by the device, after requested directly from Firebase
    """

    external_id = models.CharField(max_length=1000, unique=True)
    os = models.CharField()
    firebase_token = models.CharField(max_length=1000, null=True)


class BaseNotification(models.Model):
    """
    Data as it is sent to devices.
    - id: custom primary key
    - device_id: fk to Device.id
    - title: header of a notification (usually the name of app)
    - body: explains what the notification relates to
    - module_slug: for which (app) module was the notification created
    - context_json: tells the OS API how to handle e.g. click event, badge counter
    - pushed_at: set to true when notification was pushed successfully
    - created_at: to create an overview of the notification history
    - is_read: to be set when device has read the notification
    - notification_type: determined by service that creates the notification
    - image: loosely coupled to image service
    """

    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000)
    body = models.CharField(max_length=1000)
    module_slug = models.CharField()
    context = models.JSONField()
    notification_type = models.CharField()
    image = models.IntegerField(default=None, null=True)
    created_at = models.DateTimeField()


class ScheduledNotification(BaseNotification):
    """
    Scheduled notifications are notifications that are scheduled to be sent at a later time.
    - scheduled_at: the date the notification was scheduled at
    - scheduled_for: the date the notification was scheduled for
    - identifier: the unique identifier of the schedule starting with the module_slug
    """

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["identifier"], name="unique_identifier")
        ]

    identifier = models.CharField()
    scheduled_for = models.DateTimeField()
    device_ids = models.ManyToManyField(Device, related_name="scheduled_notifications")


class Notification(BaseNotification):
    schedule = models.ForeignKey(
        ScheduledNotification, on_delete=models.CASCADE, null=True
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    pushed_at = models.DateTimeField(auto_now_add=True)


class NotificationPushTypeEnabled(models.Model):
    """
    Record that determines if push notifications are enabled for a device.
    When no record of notification type exists for a device,
    push notifications are disabled.

    The current default settings for the Amsterdam App are:
    - In-app notifications enabled
    - Push notifications disabled

    Values:
    - device: fk to Device.id
    - notification_type: type of notification, e.g. 'construction-work:warning-message'
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    notification_type = models.CharField()


class NotificationPushServiceEnabled(models.Model):
    """
    Record that determines if push notifications are enabled for an entire module.
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    service_name = models.CharField(choices=Service.choices())
