import logging

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class ZwembadenApiService:
    def __init__(self) -> None:
        self.base_url = "https://zwembaden.api-amsterdam.nl/nl/api"

    def get_schedule_for_date_and_location(
        self, date_str: str, location_name: str
    ) -> dict:
        """Get swim schedule for a specific date and location."""
        url = f"{self.base_url}/{location_name}/date/{date_str}/"
        response = self._make_request(url)
        data = response.json()
        schedule = data.get("schedule", [])
        return schedule

    def get_activities_for_location(self, location_name: str) -> dict:
        """Get swim activities for a specific location."""
        url = f"{self.base_url}/{location_name}/activity/"
        response = self._make_request(url)
        data = response.json()
        payload = {
            "activities": data.get("activities", []),
            "schedule_per_weekday": data.get("days", []),
        }
        return payload

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self, url: str) -> requests.Response:
        """Make the HTTP request for swim schedule data with retries and a timeout."""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch swim schedule data", extra={"url": url})
            raise
