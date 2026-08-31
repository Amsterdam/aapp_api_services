import logging
from datetime import date, datetime, time

import requests
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from notification.models.notification_models import Device
from notification.models.waste_guide_models import FRACTION_COLUM_MAPPING, WasteDevice

logger = logging.getLogger(__name__)


class WasteDeviceService:
    def get_device_ids(self) -> list[str]:
        return list(WasteDevice.objects.values_list("device_id", flat=True))

    def get_postal_areas(self) -> list[str]:
        return list(
            WasteDevice.objects.exclude(postal_area__isnull=True)
            .exclude(postal_area="")
            .order_by("postal_area")
            .values_list("postal_area", flat=True)
            .distinct()
        )

    def get_device_ids_for_bag_ids(self, bag_ids: list[str]) -> list[str]:
        if not bag_ids:
            return []
        return list(
            WasteDevice.objects.filter(bag_nummeraanduiding_id__in=bag_ids).values_list(
                "device_id", flat=True
            )
        )

    def get_device_ids_for_postal_area(self, postal_area: str) -> list[str]:
        if not postal_area:
            return self.get_device_ids()
        return list(
            WasteDevice.objects.filter(postal_area=postal_area).values_list(
                "device_id", flat=True
            )
        )

    def get_device_ids_for_bag_ids_and_postal_area(
        self, bag_ids: list[str], postal_area: str | None
    ) -> list[str]:
        if not bag_ids:
            return []

        queryset = WasteDevice.objects.filter(bag_nummeraanduiding_id__in=bag_ids)
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

    def process_batch(self, batch_size: int = 50, last_pk: str = "") -> dict:
        queryset = self.get_rows_queryset().order_by("pk")
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
            "has_more": bool(rows),
        }

    def fill_empty_row(self, row: WasteDevice) -> bool:
        bag_nummeraanduiding_id = row.bag_nummeraanduiding_id
        if not bag_nummeraanduiding_id:
            logger.warning(
                f"Row with device id {row.device_id} has no bag_nummeraanduiding_id"
            )
            return False

        data = self.get_bag_nummeraanduiding_data(bag_nummeraanduiding_id)
        if not data:
            return False

        postal_area = None
        fields_to_update = []

        for fraction_data in data:
            fraction = fraction_data.get("afvalwijzerFractieCode", "").lower()
            route_name = fraction_data.get("afvalwijzerRoutenaam")
            postcode = fraction_data.get("postcode")

            if postcode and not postal_area:
                postal_area = postcode[:4]

            column_name = FRACTION_COLUM_MAPPING.get(fraction)
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

    def get_bag_nummeraanduiding_data(self, bag_nummeraanduiding_id: str) -> list:
        url = settings.WASTE_GUIDE_URL
        params = {"bagNummeraanduidingId": bag_nummeraanduiding_id}
        api_key = settings.WASTE_GUIDE_API_KEY
        headers = None

        if settings.ENVIRONMENT_SLUG in ["a", "p"]:
            headers = {"X-Api-Key": api_key}

        try:
            response_json = self.make_get_request(
                url=url,
                headers=headers,
                params=params,
            )
            return response_json.get("_embedded", {}).get("afvalwijzer", [])
        except requests.RequestException as error:
            logger.error("Error fetching waste data: %s", error)
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,
    )
    def make_get_request(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        response = requests.request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
