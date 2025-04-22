from datetime import datetime


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
