import uuid

from django.db import models


class Client(models.Model):
    """
    Entity that is open to receive push notifications.
    - external_id: provided by the client, e.g. a (hashed) device id
    - firebase_token: provided by the client, after requested directly from Firebase
    """

    external_id = models.CharField(max_length=1000, unique=True)
    os = models.CharField()
    firebase_token = models.CharField(max_length=1000, null=True)
    receive_push = models.BooleanField(default=False)


class Notification(models.Model):
    """
    Data as it is sent to clients.
    - id: custom primary key
    - client_id: loosly coupled with Client.external_id
    - title: header of a notification (usually the name of app)
    - body: explains what the notification relates to
    - module_slug: for which (app) module was the notification created
    - context_json: tells the OS API how to handle e.g. click event, badge counter
    - pushed_at: set to true when notification was pushed successfully
    - created_at: to create an overview of the notification history
    - is_read: to be set when client has read the notification
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1000)
    body = models.CharField(max_length=1000)
    module_slug = models.CharField()
    context = models.JSONField()
    client_id = models.CharField(null=True)
    created_at = models.DateTimeField()
    pushed_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
