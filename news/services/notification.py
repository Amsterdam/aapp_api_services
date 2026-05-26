from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)


class NewLiveblogNotificationService(AbstractNotificationService):
    module_slug = Module.NEWS.value
    notification_type = NotificationType.NEWS_NEW_LIVEBLOG.value

    def send(self, liveblog_title, liveblog_id):
        notification_data = NotificationData(
            title="Liveblog gestart",
            message=liveblog_title,
            link_source_id=liveblog_id,
        )
        self.upsert(notification_data, expiry_minutes=60, send_all_devices=True)
