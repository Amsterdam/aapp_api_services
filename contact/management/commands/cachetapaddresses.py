import logging

from django.core.management.base import BaseCommand

from contact.services.address import AddressService
from contact.services.taps import TapService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Warm the cached tap addresses (Amsterdam taps)"

    def handle(self, *args, **options):
        tap_service = TapService()
        address_service = AddressService()
        all_taps = tap_service.get_geojson_items()
        taps = tap_service.filter_data(all_taps)

        missing = 0
        found = 0

        for i, tap in enumerate(taps):
            if i % 50 == 0:
                logger.info(f"Processing tap {i + 1}/{len(taps)}")

            properties = tap.get("properties", {}) or {}
            lat = properties.get("latitude")
            lon = properties.get("longitude")
            address = address_service.get_address_by_coordinates(
                latitude=lat, longitude=lon
            )
            if address is None:
                missing += 1
            else:
                found += 1

        unique_coordinates = len(
            {
                (
                    (tap.get("properties", {}) or {}).get("latitude"),
                    (tap.get("properties", {}) or {}).get("longitude"),
                )
                for tap in taps
            }
        )

        logger.info(
            "Cache warm complete: "
            f"taps={len(taps)} "
            f"unique_coordinates={unique_coordinates} "
            f"addresses_found={found} "
            f"addresses_missing={missing}"
        )
