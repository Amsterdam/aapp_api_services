import copy
import json
import logging

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

from notification.models import Client, Notification

logger = logging.getLogger(__name__)


class PushServiceClientLimitError(Exception):
    """Raise when too many clients were passed"""

    pass


class PushService:
    def __init__(
        self, source_notification: Notification, client_ids: list[str]
    ) -> None:
        """
        First the Firebase admin will be initialized.
        Firebase manages its own connections, so when multiple services are initialized,
        Firebase will check if there is already an active connection setup.

        Next it will check for the limit of clients.

        Finally the supplied source_notification comes with a UUID id,
        this is reset in order to use it for duplication.

        Args:
            source_notification (Notification): Source of new notifications
            client_ids (list[str]): All clients who want to receive a notification

        Raises:
            PushServiceClientLimitError: Firebase cannot handle this many clients
        """
        if not firebase_admin._apps:
            creds = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
            firebase_admin.initialize_app(creds)
        else:
            firebase_admin.get_app()

        max_clients = settings.FIREBASE_CLIENT_LIMIT
        if len(client_ids) > max_clients:
            raise PushServiceClientLimitError(
                f"Too many clients [{len(client_ids)=}, {max_clients=}]"
            )

        self.client_ids = client_ids
        self.source_notification = source_notification
        self.source_notification.id = None

    def push(self) -> dict:
        clients = Client.objects.filter(external_id__in=self.client_ids).all()
        notifications = self.create_notifications(clients)
        response_data = self.push_messages(notifications, clients)
        response_data["total_client_count"] = len(self.client_ids)
        response_data["missing_client_ids"] = list(
            set(self.client_ids) - set([c.external_id for c in clients])
        )
        return response_data

    def create_notifications(self, clients: list[Client]) -> dict[str, Notification]:
        """
        The supplied source_notification will be duplicated for every client.

        Returns:
            list[Notification]: newly created notification objects
        """
        new_notifications = {}
        for c in clients:
            new_notification: Notification = copy.copy(self.source_notification)
            new_notification.client = c
            new_notifications[c.external_id] = new_notification

        Notification.objects.bulk_create(new_notifications.values())
        return new_notifications

    def push_messages(self, notifications: dict[str, Notification], clients) -> dict:
        """
        Forwards notification to Firebase, to be pushed to clients.

        If client has a firebase token, a Firebase message will be crafted
        and finally send as a batch to Firebase.

        Args:
            notifications (list[Notification]): notifications used for Firebase message data
        """

        clients_with_token = [c for c in clients if c.firebase_token]
        if not clients_with_token:
            logger.info(
                "Notification(s) created, but none of the clients have a Firebase token",
                extra={
                    "total_client_count": len(self.client_ids),
                },
            )
            return {
                "total_create_count": len(clients),
                "total_token_count": 0,
                "failed_token_count": 0,
            }

        firebase_messages = []
        for client in clients_with_token:
            notification_obj = notifications[client.external_id]
            message = self._define_firebase_message(client, notification_obj)
            firebase_messages.append(message)
        batch_response = messaging.send_each(firebase_messages)

        failed_tokens = []
        if batch_response.failure_count > 0:
            failed_tokens = self._log_failures(batch_response, firebase_messages)

        return {
            "total_create_count": len(clients),
            "total_token_count": len(clients_with_token),
            "failed_token_count": len(failed_tokens),
        }

    def _define_firebase_message(
        self, client: Client, notification_obj: Notification
    ) -> messaging.Message:
        complete_context = notification_obj.context
        complete_context["notificationId"] = str(notification_obj.pk)
        firebase_message = messaging.Message(
            data=complete_context,
            notification=messaging.Notification(
                title=notification_obj.title, body=notification_obj.body
            ),
            token=client.firebase_token,
        )
        return firebase_message

    def _log_failures(
        self, batch_response, firebase_messages: list[messaging.Message]
    ) -> list[str]:
        failed_tokens = []
        responses = batch_response.responses
        for idx, resp in enumerate(responses):
            if not resp.success:
                failed_token = firebase_messages[idx].token
                failed_tokens.append(failed_token)

                logger.error(
                    "Failed to send notification to client",
                    extra={
                        "firebase_token": failed_token,
                    },
                )
        return failed_tokens
