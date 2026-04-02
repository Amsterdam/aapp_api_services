import logging

import requests
from core.utils.coordinates_utils import rd_to_wgs
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
        filtered_locations = [
            location
            for location in locations
            if location.get("verhuuradministratie") == "Gemeente Amsterdam"
        ]
        # add detail name to each location dict for easier fetching of schedule and activities later on
        for location in filtered_locations:
            location = self._customize_location_dict(location)
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
            logger.info(
                "Failed to fetch swim location data", extra={"url": self.data_url}
            )
            raise

    def _customize_location_dict(self, location: dict) -> dict:
        """Customize the location dictionary to change coordinate system and add detail name."""
        rd_coordinates = location.get("geometry", {}).get("coordinates", [])
        print(f"rd_coordinates: {rd_coordinates}")
        if len(rd_coordinates) == 2:
            wgs_coordinates = rd_to_wgs(rd_coordinates[0], rd_coordinates[1])
            location["coordinates"] = {
                "lat": wgs_coordinates[1],
                "lon": wgs_coordinates[0],
            }
        else:
            location["coordinates"] = {"lat": None, "lon": None}

        location["detail_name"] = location.get("naam", "").lower().replace(" ", "-")

        # rename fields for serializer
        location["name"] = location.get("naam", "")
        location["city"] = location.get("plaats", "")
        location["street"] = location.get("adres", "").rsplit(" ", 1)[0]
        location["number"] = location.get("adres", "").split()[-1] if len(location.get("adres", "").split()) > 1 else ""
        return location
