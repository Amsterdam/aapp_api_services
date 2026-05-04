from datetime import datetime

from notification.models import Device, NotificationLast


class NotificationLastService:
    def __init__(self, module_slug: str):
        self.module_slug = module_slug

    def get_last_timestamps(self, device_id: str) -> dict[str, datetime]:
        timestamps = NotificationLast.objects.filter(
            device__external_id=device_id,
            module_slug=self.module_slug,
        )
        timestamps = {
            ts.notification_scope.removeprefix(f"{self.module_slug}:"): ts.last_create
            for ts in timestamps
        }
        return timestamps

    def update_last_timestamps(self, device_id: str, updates: dict[str, datetime]):
        device = Device.objects.get(external_id=device_id)
        notifications_last = [
            NotificationLast(
                device=device,
                module_slug=self.module_slug,
                notification_scope=f"{self.module_slug}:{service_name}",
                last_create=timestamp,
            )
            for service_name, timestamp in updates.items()
        ]
        NotificationLast.objects.bulk_create(
            notifications_last,
            update_fields=["last_create"],
            unique_fields=["device", "notification_scope"],
            update_conflicts=True,
        )

    def delete_last_timestamps(self, device_id: str):
        NotificationLast.objects.filter(
            device__external_id=device_id,
            module_slug=self.module_slug,
        ).delete()
