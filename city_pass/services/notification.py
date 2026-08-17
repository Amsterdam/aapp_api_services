import logging
from datetime import timedelta

from django.db.models import QuerySet

from city_pass.models import Notification, Session
from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)

logger = logging.getLogger(__name__)


class NotificationService(AbstractNotificationService):
    module_slug = Module.CITY_PASS.value
    notification_type = NotificationType.CITY_PASS_NOTIFICATION.value

    def send(self, notification: Notification):
        device_qs = self.get_device_qs(notification)
        notification_data = NotificationData(
            title=notification.title,
            message=notification.message,
            link_source_id=notification.pk,
            device_ids=device_qs,
        )

        if notification.send_at is not None:
            scheduled_notification = self.upsert(
                notification=notification_data,
                scheduled_for=notification.send_at,
                expires_at=notification.send_at + timedelta(minutes=30),
                identifier=self._create_identifier(notification.id),
            )

            notification.nr_sessions = scheduled_notification.devices.count()
        else:
            notification.nr_sessions = 0
        notification.save()

    def delete_notification(self, notification: Notification):
        identifier = self._create_identifier(notification.id)
        self.delete_scheduled_notification(identifier)

    def _create_identifier(self, notification_id: int) -> str:
        if not notification_id:
            raise ValueError(
                "Notification must be saved and have an id to create an identifier"
            )
        return f"{self.module_slug}_notification_{notification_id}"

    def get_device_qs(self, notification: Notification) -> QuerySet:
        budgets = list(notification.budgets.all())
        if budgets:
            sessions = Session.objects.filter(passdata__budgets__in=budgets)
        else:
            sessions = Session.objects.all()
        device_qs = (
            sessions.exclude(device_id_internal=None)
            .values_list("device_id_internal", flat=True)
            .distinct()
        )
        return device_qs
