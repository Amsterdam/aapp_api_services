import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


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
    - title: header of a notification (usually the name of app)
    - body: explains what the notification relates to
    - module_slug: for which (app) module was the notification created
    - context_json: tells the OS API how to handle e.g. click event, badge counter
    - notification_type: determined by service that creates the notification
    - image: loosely coupled to image service
    """

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["module_slug"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["created_at"]),
        ]

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
    - created_at: the timestamp on which the service created the schedule request
    - identifier: the unique identifier of the schedule starting with the module_slug
    - scheduled_for: the timestamp the notification was scheduled to be pushed
    - device_ids: m2m to Device.id
    - pushed_at: set to true when scheduled notification was processed successfully. Prevents duplicate pushes.
    """

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["identifier"], name="unique_identifier")
        ]

    identifier = models.CharField()
    scheduled_for = models.DateTimeField()
    devices = models.ManyToManyField(Device, related_name="scheduled_notifications")
    pushed_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"[SCHEDULED] {self.module_slug} - {self.title}"


class Notification(BaseNotification):
    """
    - created_at: the timestamp on which the service created the push request
    - schedule: fk to ScheduledNotification.id, only filled when the notification originated from a schedule
    - device_id: fk to Device.id
    - is_read: to be set when device has read the notification
    - pushed_at: set to true when notification was pushed successfully
    """

    schedule = models.ForeignKey(
        ScheduledNotification, on_delete=models.PROTECT, null=True
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    pushed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.module_slug} - {self.title}"


class NotificationPushTypeDisabled(models.Model):
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


class NotificationPushModuleDisabled(models.Model):
    """
    Record that determines if push notifications are enabled for an entire module.
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    module_slug = models.CharField()


class NotificationLast(models.Model):
    """
    Record that determines the last time a notification was created for a device.

    device: fk to Device.id
    module_slug: the module slug of the notification
    notification_scope: the scope of the notification, usually the notification_type
    last_create: the last time a notification was created for the device
    """

    class Meta:
        unique_together = ("device", "notification_scope")
        indexes = [
            models.Index(fields=["device", "module_slug"]),
        ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    module_slug = models.CharField()
    notification_scope = models.CharField()
    last_create = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.notification_scope.startswith(self.module_slug):
            raise ValidationError("Notification scope must start with module slug")

        if self.notification_scope not in settings.NOTIFICATION_SCOPES:
            raise ValidationError(
                f"Notification scope {self.notification_scope} is not in the list of allowed scopes"
            )
