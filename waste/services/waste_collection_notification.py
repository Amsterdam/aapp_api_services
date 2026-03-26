import logging
from datetime import date, timedelta

from django.conf import settings

from waste.services.waste_collection_abstract import WasteCollectionAbstractService

logger = logging.getLogger(__name__)


class WasteCollectionNotificationService(WasteCollectionAbstractService):
    @staticmethod
    def _get_dates() -> list[date]:
        # Only select tomorrow for date selection!
        date_tomorrow = date.today() + timedelta(days=1)
        return [date_tomorrow]

    def get_validated_data_for_route_type_code(self, route_type: str) -> list[dict]:
        """Get all records for a specific waste type from waste guide API"""

        params = {
            "afvalwijzerBasisroutetypeCode": route_type,
            "_pageSize": 20000,
        }
        next_link = settings.WASTE_GUIDE_URL
        waste_data = []
        while next_link:
            waste_data_batch, next_link = self.get_validated_data(
                url=next_link, params=params
            )
            waste_data_tomorrow = self._filter_waste_data_pickup_tomorrow(
                waste_data=waste_data_batch
            )
            waste_data.extend(waste_data_tomorrow)
            logger.info(
                f"Fetched {len(waste_data_tomorrow)} records for {route_type}, next_link: {next_link}"
            )
            params = None  # params are included in the next_link url already
        return waste_data

    def _filter_waste_data_pickup_tomorrow(self, waste_data: list[dict]) -> list[dict]:
        filtered_data = [
            item for item in waste_data if len(self.get_dates_for_waste_item(item)) > 0
        ]
        return filtered_data
