from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

ZONE_INFO = ZoneInfo(settings.TIME_ZONE)


def get_token_cut_off_for_year(year: int) -> datetime:
    cut_off_time = settings.TOKEN_CUT_OFF_DATETIME
    cut_off_datetime = datetime.strptime(f"{year}-{cut_off_time}", "%Y-%m-%d %H:%M")
    return timezone.make_aware(cut_off_datetime, ZONE_INFO)


def get_token_cut_off_for_datetime(current_datetime: datetime) -> datetime:
    amsterdam_year = timezone.localtime(current_datetime, ZONE_INFO).year
    return get_token_cut_off_for_year(amsterdam_year)


def get_token_cut_off() -> datetime:
    """
    Return the up and coming cut off datetime.
    If the current time is before the cut off datetime, the current year's cut off datetime is returned.
    If the current time is after the cut off datetime, the next year's cut off datetime is returned.

    See TOKEN_CUT_OFF_DATETIME in settings for more information.
    """
    now = timezone.localtime(timezone.now(), ZONE_INFO)
    token_cut_off_datetime = get_token_cut_off_for_year(now.year)
    if now > token_cut_off_datetime:
        token_cut_off_datetime = get_token_cut_off_for_year(now.year + 1)
    return token_cut_off_datetime
