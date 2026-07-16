import logging

from construction_work.models.manage_models import WarningMessage
from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)

logger = logging.getLogger(__name__)


class ArticleNotificationService(AbstractNotificationService):
    module_slug = Module.CONSTRUCTION_WORK.value
    notification_type = NotificationType.CONSTRUCTION_WORK_ARTICLE_MESSAGE.value

    def send(self, notification_data: NotificationData):
        context = self.build_context(
            module_slug=self.module_slug,
            notification_type=self.notification_type,
            link_source_id=notification_data.link_source_id,
            url=notification_data.url,
            deeplink=notification_data.deeplink,
        )
        context["subtype"] = "article"
        self.upsert(notification_data, context=context)


class WarningNotificationService(AbstractNotificationService):
    module_slug = Module.CONSTRUCTION_WORK.value
    notification_type = NotificationType.CONSTRUCTION_WORK_ARTICLE_MESSAGE.value

    def send(self, warning: WarningMessage):
        device_ids = list(
            warning.project.device_set.exclude(device_id=None).values_list(
                "device_id", flat=True
            )
        )

        warning_image = warning.warningimage_set.first()
        if warning_image and warning_image.image_set_id:
            image_set_id = warning_image.image_set_id
        else:
            image_set_id = None
        notification_data = NotificationData(
            title=warning.project.title,
            message=warning.title,
            link_source_id=str(warning.pk),
            device_ids=device_ids,
            image_set_id=image_set_id,
        )

        context = self.build_context(
            module_slug=self.module_slug,
            notification_type=self.notification_type,
            link_source_id=notification_data.link_source_id,
        )
        context["subtype"] = "warning"

        self.upsert(notification_data, context=context)

        warning.notification_sent = True
        warning.save()
