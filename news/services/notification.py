from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)


class NewLiveblogNotificationService(AbstractNotificationService):
    module_slug = Module.NEWS.value
    notification_type = NotificationType.NEWS_NEW_LIVEBLOG.value

    def send(self, liveblog_title: str, liveblog_id: int):
        notification_data = NotificationData(
            title="Liveblog gestart",
            message=liveblog_title,
            link_source_id=liveblog_id,
        )
        self.upsert(notification_data, expiry_minutes=60, send_all_devices=True)


class LiveblogUpdateNotificationService(AbstractNotificationService):
    module_slug = Module.NEWS.value
    notification_type = NotificationType.NEWS_LIVEBLOG_UPDATE.value

    def send(
        self,
        device_ids: list[str],
        update_title: str,
        liveblog_id: int,
        image_set_id: int | None = None,
    ):
        notification_data = NotificationData(
            title="Liveblog update",
            message=update_title,
            link_source_id=liveblog_id,
            device_ids=device_ids,
            image_set_id=image_set_id,
        )
        self.upsert(notification_data, expiry_minutes=60)
