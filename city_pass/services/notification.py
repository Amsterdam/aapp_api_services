import logging

from django.utils import timezone

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
        device_ids = self.get_device_ids(notification)
        notification_data = NotificationData(
            title=notification.title,
            message=notification.message,
            link_source_id=notification.pk,
            device_ids=device_ids,
        )

        self.process(notification_data)

        notification.send_at = timezone.now()
        notification.nr_sessions = len(device_ids)
        notification.save()

    def get_device_ids(self, notification: Notification):
        budgets = list(notification.budgets.all())
        if budgets:
            sessions = Session.objects.filter(passdata__budgets__in=budgets)
        else:
            sessions = Session.objects.all()
        device_ids = (
            sessions.exclude(device_id=None)
            .values_list("device_id", flat=True)
            .distinct()
        )
        return list(device_ids)
