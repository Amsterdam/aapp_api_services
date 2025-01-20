import uuid

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


class ImageVariant(models.Model):
    """
    Image model.
    - image: the actual image
    - description: optional description of the image
    - width: width of the image in pixels
    - height: height of the image in pixels
    """

    image = models.ImageField(upload_to="notification/images/")
    width = models.IntegerField()
    height = models.IntegerField()

    def save(self, *args, **kwargs):
        self.width = self.image.width
        self.height = self.image.height
        super().save(*args, **kwargs)


class ImageSet(models.Model):
    """
    Group of images.
    - firebase_image: image for Firebase
    - thumbnail_image: thumbnail image
    - large_image: large image
    """

    description = models.CharField(max_length=1000, blank=True, null=True)
    firebase_image = models.ForeignKey(
        ImageVariant, on_delete=models.CASCADE, related_name="firebase"
    )
    thumbnail_image = models.ForeignKey(
        ImageVariant, on_delete=models.CASCADE, related_name="thumbnail"
    )
    large_image = models.ForeignKey(
        ImageVariant, on_delete=models.CASCADE, related_name="large"
    )


class Notification(models.Model):
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
    - image_set: fk to ImageSet.id
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000)
    body = models.CharField(max_length=1000)
    module_slug = models.CharField()
    context = models.JSONField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    pushed_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    image_set = models.ForeignKey(
        ImageSet, on_delete=models.CASCADE, null=True, blank=True
    )
