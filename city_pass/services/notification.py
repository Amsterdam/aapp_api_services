import logging

from django.db.models import QuerySet
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
        device_qs = self.get_device_qs(notification)
        notification_data = NotificationData(
            title=notification.title,
            message=notification.message,
            link_source_id=notification.pk,
            device_ids=device_qs,
        )

        self.upsert(notification_data)

        notification.send_at = timezone.now()
        notification.nr_sessions = device_qs.count()
        notification.save()

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
