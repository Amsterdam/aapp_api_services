import logging

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class DataAmsterdamService:
    def __init__(self) -> None:
        self.data_url = "https://api.data.amsterdam.nl/v1/sport/v1/zwembad"

    def get_swim_locations_where_amsterdam_is_renting_out(self) -> list:
        """Get swim locations where Amsterdam is renting out."""
        response = self._make_request()
        data = response.json()
        locations = data.get("_embedded", {}).get("zwembad", [])
        filtered_locations = [location for location in locations if location.get("verhuuradministratie") == "Gemeente Amsterdam"]
        # add detail name to each location dict for easier fetching of schedule and activities later on
        for location in filtered_locations:
            location["detail-name"] = location.get("naam").lower().replace(" ", "-")
        return filtered_locations

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self) -> requests.Response:
        """Make the HTTP request for swim location data with retries and a timeout."""
        try:
            response = requests.get(self.data_url, timeout=5)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch swim location data", extra={"url": self.data_url})
            raise
