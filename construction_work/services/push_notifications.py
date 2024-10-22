import json
import logging
from typing import Tuple

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

from construction_work.models import Notification, WarningMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Send notifications through Firebase (by Google)"""

    def __init__(
        self,
        warning: WarningMessage,
        batch_size=500,
    ):
        if not firebase_admin._apps:
            creds = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
            firebase_admin.initialize_app(creds)
        else:
            firebase_admin.get_app()

        self.warning = warning
        self.batch_size = batch_size
        self.firebase_tokens = None
        self.failed_tokens = []

    def collect_tokens(self) -> bool:
        """Collect tokens from related devices, return False if no tokens are found"""
        self.firebase_tokens = self.warning.project.device_set.exclude(
            firebase_token=None
        ).values_list("firebase_token", flat=True)

        if not self.firebase_tokens.exists():
            logger.info(
                f"No firebase tokens found for project [{self.warning.project.pk=}]"
            )
            return False
        return True

    def get_success_rate(self) -> Tuple[int, int]:
        """
        Get success rate
        E.g. of 100 tokens, 75 failed, so success rate is 25/100
        """
        all_tokens_len = len(self.firebase_tokens)
        failed_tokens_len = len(self.failed_tokens)
        success_tokens_len = all_tokens_len - failed_tokens_len
        return success_tokens_len, all_tokens_len

    @staticmethod
    def _tokens_in_batches(tokens, batch_size):
        return [tokens[x : x + batch_size] for x in range(0, len(tokens), batch_size)]

    def push(self):
        """Send message to subscribers, return failed tokens"""
        notification = Notification(
            title=self.warning.project.title,
            body=self.warning.title,
            warning=self.warning,
        )

        self.failed_tokens = []
        for token_batch in self._tokens_in_batches(
            self.firebase_tokens, self.batch_size
        ):
            message = messaging.MulticastMessage(
                data={
                    "linkSourceid": str(self.warning.pk),
                    "type": "ProjectWarningCreatedByProjectManager",
                },
                notification=messaging.Notification(
                    title=notification.title, body=notification.body
                ),
                tokens=token_batch,
            )

            batch_response = messaging.send_each_for_multicast(message)
            if batch_response.failure_count > 0:
                responses = batch_response.responses
                for idx, resp in enumerate(responses):
                    if not resp.success:
                        # The order of responses corresponds to the order of the registration tokens.
                        self.failed_tokens.append(token_batch[idx])

        # Create notification in database
        notification.save()


def trigger_push_notification(warning: WarningMessage) -> Tuple[bool, str]:
    """
    Trigger the push notification services

    First return variable tells if pushing was ok, so no issues
    Second return variable tells why pusing was or wasn't ok
    """
    relevant_data_for_logs = (
        f"{warning.title=}, {warning.project.pk=}, {warning.project_manager.email=}"
    )

    # Check if notification was already sent for this warning
    # Only relevent when updating a existing warning
    if Notification.objects.filter(warning=warning).exists():
        info_message = "Notification already sent for this warning"
        logger.info(f"{info_message} [{relevant_data_for_logs}]")
        return True, info_message

    try:
        notification_service = NotificationService(warning)
    except Exception as e:
        error_message = str(e)
        logger.error(f"{error_message} [{relevant_data_for_logs}]")
        return False, error_message

    setup_success = notification_service.collect_tokens()

    # Check if devices are subscribed to the related project
    if setup_success is False:
        info_message = """No notification will be sent, \
            since no firebase tokens were retrieved from related devices \
            or no related devices were found"""
        logger.info(f"{info_message} [{relevant_data_for_logs}]")
        # Its okay that no firebase tokens were found
        return True, info_message

    # Send notifications, capture possible failed tokens
    try:
        notification_service.push()
        success_count, total_count = notification_service.get_success_rate()
        success_rate_str = f"{success_count}/{total_count}"
        if success_count < total_count:
            final_message = f"Sending notification failed for some tokens, success rate: {success_rate_str}"
            logger.warning(f"{final_message} [{relevant_data_for_logs}]")
        else:
            final_message = f"Sending notifications to all tokens successful, success rate: {success_rate_str}"
            logger.info(f"{final_message} [{relevant_data_for_logs}]")

        return True, final_message
    # Firebase is external dependency so might throw exception for some reason
    except Exception as e:
        error_message = str(e)
        logger.error(f"{error_message} [{relevant_data_for_logs}]")
        return False, error_message
