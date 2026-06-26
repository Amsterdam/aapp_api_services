from datetime import timedelta

from django.conf import settings


def get_thresholds():
    base = [
        parse_duration(t)
        for t in settings.BOAT_CHARGING_NOTIFICATION_SETTINGS["thresholds"].split(",")
    ]

    repeat = parse_duration(
        settings.BOAT_CHARGING_NOTIFICATION_SETTINGS["repeat_every"]
    )

    return base, repeat


def parse_duration(value: str) -> timedelta:
    value = value.upper().strip()

    if value.endswith("D"):
        return timedelta(days=int(value[:-1]))
    if value.endswith("H"):
        return timedelta(hours=int(value[:-1]))
    if value.endswith("M"):
        return timedelta(minutes=int(value[:-1]))

    raise ValueError(f"Invalid duration format: {value}")
