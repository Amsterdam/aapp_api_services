import datetime
import logging
from datetime import timedelta

from django.utils import timezone

from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from core.services.waste_device import (
    FRACTION_COLUMN_MAPPING,
    WasteDevice,
    WasteDeviceService,
)
from waste.models import ManualNotification
from waste.services.waste_collection import WasteCollectionService

logger = logging.getLogger(__name__)


class NotificationService(AbstractNotificationService):
    module_slug = Module.WASTE.value
    notification_type = NotificationType.WASTE_DATE_REMINDER.value

    def __init__(self):
        super().__init__()
        self.notification_datetime = datetime.datetime.combine(
            datetime.date.today(), datetime.time(hour=21, minute=0)
        )

    def send(
        self,
        device_ids: list[str],
        waste_type: str,
        notification_datetime: datetime.datetime | None = None,
    ):

        notification = NotificationData(
            title="Afvalwijzer",
            message=f"Morgen halen we {waste_type.lower()} in uw buurt op. Ga naar Afvalwijzer.",
            device_ids=device_ids,
        )

        self.upsert(
            notification=notification,
            scheduled_for=notification_datetime or self.notification_datetime,
            identifier=self._create_identifier(waste_type=waste_type),
        )

    def _create_identifier(self, waste_type: str) -> str:
        return f"{Module.WASTE.value}_{waste_type.replace(' ', '-')}_reminder"


class ManualNotificationService(AbstractNotificationService):
    module_slug = Module.WASTE.value
    notification_type = NotificationType.WASTE_MANUAL_NOTIFICATION.value
    waste_device_service = WasteDeviceService()
    waste_collection_service = WasteCollectionService()

    def send(self, notification: ManualNotification):
        device_ids = self.get_device_ids(notification)
        if len(device_ids) > 0:
            notification_data = NotificationData(
                title=notification.title,
                message=notification.message,
                link_source_id=notification.pk,
                device_ids=device_ids,
            )
            scheduled_notification = self.upsert(
                notification=notification_data,
                scheduled_for=notification.send_at,
                expires_at=notification.send_at + timedelta(minutes=30),
                identifier=self._create_identifier(notification.id),
            )
            notification.nr_sessions = scheduled_notification.devices.count()
        else:
            notification.nr_sessions = 0

        notification.save(update_fields=["nr_sessions"])

    def delete_notification(self, notification: ManualNotification):
        identifier = self._create_identifier(notification.id)
        self.delete_scheduled_notification(identifier)

    def _create_identifier(self, notification_id: int) -> str:
        if not notification_id:
            raise ValueError(
                "Notification must be saved and have an id to create an identifier"
            )
        return f"{self.module_slug}_notification_{notification_id}"

    def get_device_ids(self, obj: ManualNotification) -> list[str]:
        route_names = list(obj.affected_routes.values_list("name", flat=True))
        postal_area = obj.affected_postal_area
        bag_ids = (
            self.waste_device_service.get_device_ids_for_route_names_and_postal_area(
                route_names, postal_area
            )
        )
        return list(set(bag_ids))

    def process_batch(self, batch_size: int = 50, last_pk: str = "") -> dict:
        queryset = self.waste_device_service.get_rows_queryset().order_by("pk")
        if last_pk:
            queryset = queryset.filter(pk__gt=last_pk)

        rows = list(queryset[:batch_size])

        processed = 0
        updated = 0
        skipped = 0
        failed = 0

        for row in rows:
            processed += 1
            try:
                was_updated = self.fill_empty_row(row)
            except Exception:  # pragma: no cover
                logger.exception(
                    f"Unexpected error while updating waste device {row.pk}"
                )
                failed += 1
                continue

            if was_updated:
                updated += 1
            else:
                skipped += 1

        return {
            "processed": processed,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
            "last_pk": str(rows[-1].pk) if rows else last_pk,
            "has_more": len(rows) == batch_size,
        }

    def fill_empty_row(self, row: WasteDevice) -> bool:
        bag_nummeraanduiding_id = row.bag_nummeraanduiding_id
        if not bag_nummeraanduiding_id:
            logger.warning(
                f"Row with device id {row.device_id} has no bag_nummeraanduiding_id"
            )
            return False

        data = self.waste_collection_service.get_validated_data_for_bag_id(
            bag_nummeraanduiding_id
        )
        if not data:
            return False

        postal_area = None
        fields_to_update = []

        for fraction_data in data:
            fraction = fraction_data.get("code", "").lower()
            route_name = fraction_data.get("route_name")
            postcode = fraction_data.get("postal_code")

            if postcode and not postal_area:
                postal_area = postcode[:4]

            column_name = FRACTION_COLUMN_MAPPING.get(fraction)
            if not column_name:
                logger.warning(f"Unmapped fraction code '{fraction}'")
            if column_name and route_name:
                field_name = f"route_name_{column_name}"
                setattr(row, field_name, route_name)
                if field_name not in fields_to_update:
                    fields_to_update.append(field_name)

        if postal_area:
            row.postal_area = postal_area
            fields_to_update.append("postal_area")

        if not fields_to_update:
            return False

        row.routes_updated_at = timezone.now()
        fields_to_update.append("routes_updated_at")
        row.save(update_fields=fields_to_update)
        return True
