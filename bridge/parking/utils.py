from datetime import datetime

from bridge.parking.services.ssp import SSPEndpoint


def parse_iso_datetime(date_time_str: str) -> datetime:
    """
    Convert ISO 8601 datetime string to datetime object.
    Accepts timezone notation as Z (UTC), will convert to "+00:00" (UTC).
    """
    try:
        date_time_str = date_time_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_time_str)
    except ValueError as e:
        raise ValueError(f"Invalid ISO 8601 datetime string: {date_time_str}") from e


def mock_ssp_api_call(
    method, endpoint, data, ssp_access_token=None
):  # pragma: no cover
    """Mock SSP API call"""
    mock_response = {}
    if endpoint == SSPEndpoint.ORDERS:
        mock_response = {
            "frontendId": 1234567890,
            "redirectUrl": "https://www.foo.bar",
            "orderStatus": "Initiated",
            "orderType": "Parking",
        }
    return mock_response
