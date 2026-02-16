import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from core.validators import context_validator


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000)
    body = models.CharField(max_length=1000)
    module_slug = models.CharField()
    context = models.JSONField(validators=[context_validator])
    notification_type = models.CharField()
    image = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        # note: save is not called when using bulk_create or bulk_update
        if not self.context:
            self.context = {
                "type": self.notification_type,
                "module_slug": self.module_slug,
            }

        # make sure validation is actually triggered when saving a notification instance,
        self.full_clean()
        super().save(*args, **kwargs)


class ScheduledNotification(BaseNotification):
    """
    Scheduled notifications are notifications that are scheduled to be sent at a later time.
    - created_at: the timestamp on which the service created the schedule request
    - identifier: the unique identifier of the schedule starting with the module_slug
    - scheduled_for: the timestamp the notification was scheduled to be pushed
    - device_ids: m2m to Device.id
    """

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["identifier"], name="unique_identifier"),
            models.CheckConstraint(
                check=Q(expires_at__gt=F("scheduled_for")),
                name="expires_after_scheduled_for",
            ),
        ]
        indexes = [
            models.Index(fields=["module_slug"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["scheduled_for"]),
        ]

    identifier = models.CharField()
    scheduled_for = models.DateTimeField()
    devices = models.ManyToManyField(Device, related_name="scheduled_notifications")
    expires_at = models.DateTimeField(default="3000-01-01")
    make_push = models.BooleanField(default=True)

    def __str__(self):
        return f"[SCHEDULED] {self.module_slug} - {self.title}"


class Notification(BaseNotification):
    """
    - created_at: the timestamp on which the service created the push request
    - device_id: fk to Device.id
    - is_read: to be set when device has read the notification
    - pushed_at: set to true when notification was pushed successfully
    """

    class Meta:
        indexes = [
            models.Index(fields=["module_slug"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["device_external_id"]),
        ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    device_external_id = models.CharField(max_length=1000)
    is_read = models.BooleanField(default=False)
    pushed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.module_slug} - {self.title}"

    def save(self, *args, **kwargs):
        self.device_external_id = self.device.external_id
        super().save()


class NotificationPushTypeDisabled(models.Model):
    """
    Record that determines if push notifications are enabled for a device.
    When no record of notification type exists for a device,
    push notifications are disabled.

    The current default settings for the Amsterdam App are:
    - In-app notifications enabled
    - Push notifications enabled

    Values:
    - device: fk to Device.id
    - notification_type: type of notification, e.g. 'construction-work:warning-message'
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    notification_type = models.CharField()

    class Meta:
        unique_together = ("device", "notification_type")


class NotificationPushModuleDisabled(models.Model):
    """
    Record that determines if push notifications are enabled for an entire module.
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    module_slug = models.CharField()

    class Meta:
        unique_together = ("device", "module_slug")


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
