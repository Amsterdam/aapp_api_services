import logging
from datetime import date, timedelta

from django.conf import settings

from waste.interpret_frequencies import interpret_frequencies
from waste.services.waste_collection_abstract import WasteCollectionAbstractService

logger = logging.getLogger(__name__)


class WasteCollectionNotificationService(WasteCollectionAbstractService):
    def get_validated_data_for_route_type_code(
        self, route_type: str, page_size: int
    ) -> list[dict]:
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
        """
        Only filtering on day is not enough, as some pickups are scheduled every other week
        or every 4 weeks for example, and we don't want to send notifications for those.
        Therefore, we also need to check the "afvalwijzerAfvalkalenderFrequentie" field,
        which contains frequency information.
        """
        filtered_data = [
            d
            for d in waste_data
            if self._is_pickup_tomorrow(
                frequency=d.get("frequency", "") or "",
                note=d.get("note", "") or "",
            )
        ]
        return filtered_data

    def _is_pickup_tomorrow(self, frequency: str, note: str) -> bool:
        date_tomorrow = date.today() + timedelta(days=1)
        weekday_tomorrow = date_tomorrow.weekday()
        dates = interpret_frequencies(
            dates=[date_tomorrow],
            frequency=frequency,
            note=note,
            ophaaldagen_list=[weekday_tomorrow],
        )
        return len(dates) > 0
