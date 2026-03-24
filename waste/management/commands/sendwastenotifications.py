import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.services.waste_device import WasteDeviceService
from waste.constants import WASTE_COLLECTION_ROUTE_TYPES
from waste.interpret_frequencies import interpret_frequencies
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

        self.waste_device_service = WasteDeviceService()
        self.notification_service = NotificationService()
        self.notification_schedules = (
            self.waste_device_service.get_outdated_waste_devices()
        )
        logger.info(
            "Initialized command.",
            extra=dict(
                total_registered_devices=len(self.notification_schedules),
            ),
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
            logger.info(f"Fetching data for {waste_type_route}")
            full_data.extend(
                self._get_records_for_waste_type(
                    waste_type=waste_type_route, page_size=20000
                )
            )
        logger.info("Fetched all waste data from Waste Guide API.")

        devices_per_fraction = self._get_devices_per_fraction(filtered_data=full_data)
        logger.info(f"Got all device IDs for {len(devices_per_fraction)} waste types.")

        self._send_notifications(fraction_device_ids=devices_per_fraction)
        logger.info("Sent all notifications, now update schedules.")

        # Mark all schedules as updated, to prevent sending the same notification multiple times
        ids_to_update = [schedule.pk for schedule in self.notification_schedules]
        self.waste_device_service.update_waste_device(ids_to_update=ids_to_update)

    def _get_records_for_waste_type(
        self, waste_type: str, page_size: int
    ) -> list[dict]:
        """Get all records for a specific waste type from waste guide API"""

        params = {
            "afvalwijzerBasisroutetypeCode": waste_type,
            "_pageSize": page_size,
        }
        next_link = self.url
        waste_data = []
        while next_link:
            waste_data_batch, next_link = self._get_response_data(
                url=next_link, headers=self.headers, params=params
            )

            # trim and filter waste data to only keep records with a pickup day
            waste_data_batch = self._trim_waste_data_fields(waste_data=waste_data_batch)
            waste_data_batch = self._filter_waste_data_picked_up_tomorrow(
                waste_data=waste_data_batch
            )
            waste_data.extend(waste_data_batch)
            logger.info(
                f"Fetched {len(waste_data_batch)} records for {waste_type}, next_link: {next_link}"
            )
            params = None
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
        except requests.exceptions.RequestException as e:
            logger.error(
                "Error fetching data from Waste Guide API",
                extra={"url": url},
                exc_info=e,
            )
            return [], None

        waste_data = response_json.get("_embedded", {}).get("afvalwijzer", [])
        next_link = response_json.get("_links", {}).get("next", {}).get("href")
        return waste_data, next_link

    @retry(
        stop=stop_after_attempt(3),  # Retry up to 3 times
        wait=wait_fixed(2),  # Wait 2 seconds between retries
        retry=retry_if_exception_type(
            requests.exceptions.RequestException
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
        resp = requests.get(url, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        response_json = resp.json()
        return response_json

    def _trim_waste_data_fields(self, waste_data: list[dict]) -> list[dict]:
        """Filter out required data fields from waste data"""
        required_fields = [
            "bagNummeraanduidingId",
            "afvalwijzerFractieNaam",
            "afvalwijzerOphaaldagen2",
            "afvalwijzerAfvalkalenderFrequentie",
            "afvalwijzerAfvalkalenderOpmerking",
        ]
        trimmed_data = [
            {key: item for key, item in d.items() if key in required_fields}
            for d in waste_data
        ]
        return trimmed_data

    def _filter_waste_data_picked_up_tomorrow(
        self, waste_data: list[dict]
    ) -> list[dict]:
        """
        Only filtering on day is not enough, as some pickups are scheduled every other week
        or every 4 weeks for example, and we don't want to send notifications for those.
        Therefore we also need to check the "afvalwijzerAfvalkalenderFrequentie" field,
        which contains frequency information.
        """
        filtered_data = [
            d
            for d in waste_data
            if self._pickup_day_is_tomorrow(
                frequency=d.get("afvalwijzerAfvalkalenderFrequentie", "") or "",
                note=d.get("afvalwijzerAfvalkalenderOpmerking", "") or "",
            )
        ]
        return filtered_data

    def _pickup_day_is_tomorrow(self, frequency: str, note: str) -> date | None:
        date_tomorrow = date.today() + timedelta(days=1)
        weekday_tomorrow = date_tomorrow.weekday()
        dates = interpret_frequencies(
            dates=[date_tomorrow],
            frequency=frequency,
            note=note,
            ophaaldagen_list=[weekday_tomorrow],
        )
        if len(dates) == 0:
            return None
        return dates[0]

    def _get_devices_per_fraction(
        self, filtered_data: list[dict]
    ) -> dict[str, list[str]]:
        """Check for filtered data if there are devices registered for the bag nummeraanduiding
        collect all device_ids for the ones that match"""
        devices_per_fraction = defaultdict(list)
        device_ids_per_bag_id = self._get_device_ids_per_bag_id()
        for data in filtered_data:
            bag_nummeraanduiding_id = data.get("bagNummeraanduidingId", "") or ""
            # get waste type from data
            fraction = data.get("afvalwijzerFractieNaam")
            if not fraction:
                logger.warning(
                    "No waste type found. Skipping notification.",
                    extra={"bag_nummeraanduiding_id": bag_nummeraanduiding_id},
                )
                continue
            device_ids = device_ids_per_bag_id[bag_nummeraanduiding_id]
            devices_per_fraction[fraction] += device_ids
        return devices_per_fraction

    def _get_device_ids_per_bag_id(self):
        """Filter notification schedules to only those that need to be sent"""
        device_ids_per_bag_id = defaultdict(list)
        for schedule in self.notification_schedules:
            device_ids_per_bag_id[schedule.bag_nummeraanduiding_id].append(
                schedule.device_id
            )
        return device_ids_per_bag_id

    def _send_notifications(self, fraction_device_ids: dict[str, list[str]]):
        """send notifications to all device ids"""
        for waste_type, device_ids in fraction_device_ids.items():
            deduplicated_device_ids = list(set(device_ids))
            if deduplicated_device_ids:
                self.notification_service.send(
                    device_ids=deduplicated_device_ids,
                    waste_type=waste_type,
                )
                logger.info(
                    f"Scheduled notifications for {waste_type} - {len(deduplicated_device_ids)} devices",
                    extra={
                        "type": waste_type,
                        "nr_devices": len(deduplicated_device_ids),
                    },
                )
