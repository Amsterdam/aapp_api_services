import datetime
import logging
from typing import Any

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from waste.constants import (
    WASTE_COLLECTION_ROUTE_TYPES,
    WASTE_TYPES_MAPPING_READABLE,
    WEEKDAYS,
)
from waste.models import NotificationSchedule
from waste.services.notification import NotificationService


class WasteCollectionError(Exception):
    pass


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send notifications for Waste"""

    help = "Send notifications for waste"

    def __init__(self):
        super().__init__()
        self.url = settings.WASTE_GUIDE_URL
        self.api_key = settings.WASTE_GUIDE_API_KEY
        self.headers = None
        if settings.ENVIRONMENT_SLUG in ["a", "p"]:
            self.headers = {"X-Api-Key": self.api_key}
        self.tomorrow_weekday_name = WEEKDAYS[
            (datetime.date.today() + datetime.timedelta(days=1)).weekday()
        ]
        self.notification_datetime = datetime.datetime.combine(
            datetime.date.today(), datetime.time(hour=21, minute=0)
        )  # send at 21:00 today for tomorrow pickups
        self.notification_service = NotificationService()
        self.notification_schedules = list(
            NotificationSchedule.objects.filter(
                Q(
                    updated_at__lt=datetime.datetime.combine(
                        datetime.date.today(), datetime.time.min
                    )
                )
                | Q(updated_at__isnull=True)
            )
        )
        logger.info(
            f"[waste-notification] Initialized command."
            f"\nReady to send notifications for '{self.tomorrow_weekday_name}'."
            f"\nNotifications will be send at {self.notification_datetime}"
            f"\nTotal devices registered: {len(self.notification_schedules)}"
        )

    def handle(self, *args, **options):
        """
        This function is called when the management command is executed.
        It loads all waste collection records for different waste types,
        filters them based on whether the pickup day is tomorrow, collects device IDs
        for notifications, and schedules the notifications accordingly.
        """
        full_data = []
        for waste_type_route in WASTE_COLLECTION_ROUTE_TYPES:
            logger.info(f"[waste-notification] Fetching data for {waste_type_route}")
            full_data.extend(
                self._get_records_for_waste_type(
                    waste_type=waste_type_route, page_size=20000
                )
            )
        logger.info("[waste-notification] Fetched all waste data from Waste Guide API.")
        fraction_device_ids = self._get_devices_per_waste_type(filtered_data=full_data)
        logger.info(
            f"[waste-notification] Got all device IDs for {len(fraction_device_ids.items())} waste types."
        )
        self._send_notifications(fraction_device_ids=fraction_device_ids)
        logger.info(
            "[waste-notification] Sent all notifications, now update schedules."
        )

        # Mark all schedules as updated, to prevent sending the same notification multiple times
        ids_to_update = [schedule.pk for schedule in self.notification_schedules]
        NotificationSchedule.objects.filter(pk__in=ids_to_update).update(
            updated_at=timezone.now()
        )

    def _get_records_for_waste_type(
        self, waste_type: str, page_size: int = 5000
    ) -> list[dict]:
        """Get all records for a specific waste type from waste guide API"""

        # get data of first page
        params = {
            "afvalwijzerBasisroutetypeCode": waste_type,
            "_pageSize": page_size,
        }
        waste_data, next_link = self._get_response_data(
            url=self.url, headers=self.headers, params=params
        )
        logger.info(
            f"[waste-notification] Fetched {len(waste_data)} records for {waste_type}, next_link: {next_link}"
        )

        # get data of all the next pages
        while next_link:
            data_part, next_link = self._get_response_data(
                url=next_link, headers=self.headers
            )
            waste_data.extend(data_part)
            logger.info(
                f"[waste-notification] Fetched {len(waste_data)} records for {waste_type}, next_link: {next_link}"
            )

        return waste_data

    def _get_response_data(
        self,
        url: str,
        headers: dict[str, str] | None,
        params: dict[str, str] | None = None,
    ) -> tuple[list[dict], str | None]:
        """Get response data from waste guide API.

        Make request and return waste data and next link"""

        try:
            response_json = self._make_request(url=url, headers=headers, params=params)
        except WasteCollectionError as e:
            logger.error(
                f"[waste-notification] Error fetching data from Waste Guide API for {url}: {e}"
            )
            return [], None

        waste_data = response_json.get("_embedded", {}).get("afvalwijzer", [])

        # filter waste data to only keep records with a pickup day
        waste_data = self._filter_waste_data_on_day(data=waste_data)
        next_link = response_json.get("_links", {}).get("next", {}).get("href")
        return waste_data, next_link

    def _filter_waste_data_on_day(self, data: list[dict]) -> list[dict]:
        """filter on day, to only keep the records where pickupday is tomorrow, also only keep relevant fields"""
        filtered_data = [
            {
                "bagNummeraanduidingId": d.get("bagNummeraanduidingId", ""),
                "afvalwijzerFractieCode": d.get("afvalwijzerFractieCode", ""),
                "afvalwijzerOphaaldagen2": d.get("afvalwijzerOphaaldagen2", ""),
            }
            for d in data
            if self.tomorrow_weekday_name
            in (d.get("afvalwijzerOphaaldagen2", "") or "")
        ]
        return filtered_data

    @retry(
        stop=stop_after_attempt(3),  # Retry up to 3 times
        wait=wait_fixed(2),  # Wait 2 seconds between retries
        retry=retry_if_exception_type(
            WasteCollectionError
        ),  # Retry only on custom exceptions
    )
    def _make_request(
        self,
        url: str,
        headers: dict[str, str] | None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Get response data from waste guide API.

        Make request and return waste data and next link"""

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=60)
            resp.raise_for_status()
            response_json = resp.json()
            return response_json
        except requests.exceptions.RequestException as e:
            logger.error(
                f"[waste-notification] Error fetching data from Waste Guide API for {url}: {e}"
            )
            raise WasteCollectionError from e

    def _get_devices_per_waste_type(
        self, filtered_data: list[dict]
    ) -> dict[str, list[str]]:
        """Check for filtered data if there are devices registered for the bag nummeraanduiding
        collect all device_ids for the ones that match"""
        fraction_device_ids = {}
        for data in filtered_data:
            bag_nummeraanduiding_id = data.get("bagNummeraanduidingId", "") or ""
            scheduled_notifications = self._filter_notifications_to_send(
                bag_nummeraanduiding_id=bag_nummeraanduiding_id
            )
            for scheduled_notification in scheduled_notifications:
                # get waste type from data
                waste_type = WASTE_TYPES_MAPPING_READABLE.get(
                    data.get("afvalwijzerFractieCode")
                )
                if waste_type not in fraction_device_ids.keys():
                    fraction_device_ids[waste_type] = [scheduled_notification.device_id]
                else:
                    fraction_device_ids[waste_type].append(
                        scheduled_notification.device_id
                    )
        return fraction_device_ids

    def _filter_notifications_to_send(
        self, bag_nummeraanduiding_id: str
    ) -> list[NotificationSchedule]:
        """Filter notification schedules to only those that need to be sent"""
        return [
            schedule
            for schedule in self.notification_schedules
            if schedule.bag_nummeraanduiding_id == bag_nummeraanduiding_id
        ]

    def _send_notifications(self, fraction_device_ids: dict[str, list[str]]):
        # send notifications to all device ids
        for waste_type, device_ids in fraction_device_ids.items():
            deduplicated_device_ids = list(set(device_ids))
            self.notification_service.send_waste_notification(
                device_ids=deduplicated_device_ids,
                waste_type=waste_type,
                notification_datetime=self.notification_datetime,
            )
            logger.info(
                f"[waste-notification] Scheduled notifications for {waste_type} - {len(deduplicated_device_ids)} devices",
                extra={"type": waste_type, "nr_devices": len(deduplicated_device_ids)},
            )
