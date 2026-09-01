import logging
from datetime import date, datetime, time

from django.db.models import Max, Q
from django.utils import timezone

from notification.models.notification_models import Device
from notification.models.waste_guide_models import (
    FRACTION_COLUMN_MAPPING as FRACTION_COLUMN_MAPPING,
)
from notification.models.waste_guide_models import (
    WasteDevice,
)

logger = logging.getLogger(__name__)


class WasteDeviceService:
    def get_device_ids(self) -> list[str]:
        return list(WasteDevice.objects.values_list("device_id", flat=True))

    def get_device_ids_for_route_names_and_postal_area(
        self, route_names: list[str] | None, postal_area: str | None
    ) -> list[str]:
        queryset = self.get_rows_queryset()
        if route_names:
            queryset = queryset.filter(
                Q(route_name_bulk__in=route_names)
                | Q(route_name_glas__in=route_names)
                | Q(route_name_organic__in=route_names)
                | Q(route_name_paper__in=route_names)
                | Q(route_name_plastic__in=route_names)
                | Q(route_name_residual__in=route_names)
                | Q(route_name_textile__in=route_names)
            )
        if postal_area:
            queryset = queryset.filter(postal_area=postal_area)
        return list(queryset.values_list("device_id", flat=True))

    def bulk_create_waste_devices(self, waste_devices: list[WasteDevice]):
        WasteDevice.objects.bulk_create(waste_devices)

    def ensure_devices_exist(self, device_ids: list[str]) -> None:
        existing_external_ids = set(
            Device.objects.filter(external_id__in=device_ids).values_list(
                "external_id", flat=True
            )
        )
        missing_external_ids = set(device_ids) - existing_external_ids

        if missing_external_ids:
            Device.objects.bulk_create(
                [
                    Device(external_id=external_id, os="unknown")
                    for external_id in missing_external_ids
                ],
                ignore_conflicts=True,
            )

    def define_waste_device_instance(
        self, device_id: str, bag_nummeraanduiding_id: str, updated_at: datetime
    ) -> WasteDevice:
        return WasteDevice(
            device_id=device_id,
            bag_nummeraanduiding_id=bag_nummeraanduiding_id,
            updated_at=updated_at,
        )

    def get_outdated_waste_devices(self) -> list[WasteDevice]:
        # add filtering on bag_nummeraanduiding_id to only get devices that are relevant for the notifications
        return list(
            WasteDevice.objects.filter(
                (
                    Q(updated_at__lt=datetime.combine(date.today(), time.min))
                    | Q(updated_at__isnull=True)
                )
                & Q(bag_nummeraanduiding_id__isnull=False)
            )
        )

    def update_waste_device(self, ids_to_update: list[str]):
        WasteDevice.objects.filter(pk__in=ids_to_update).update(
            updated_at=timezone.now()
        )

    def get_rows_queryset(self):
        return WasteDevice.objects.all()

    def get_total_rows(self) -> int:
        return self.get_rows_queryset().count()

    def get_rows_without_route_updated_at(self):
        return WasteDevice.objects.filter(routes_updated_at__isnull=True)

    def get_rowcount_without_route_updated_at(self):
        return self.get_rows_without_route_updated_at().count()

    def get_latest_route_updated_at(self):
        return WasteDevice.objects.aggregate(latest=Max("routes_updated_at"))["latest"]
