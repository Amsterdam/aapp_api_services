from datetime import datetime

from django.conf import settings
from django.utils import timezone


def get_token_cut_off() -> datetime:
    """
    Return the up and coming cut off datetime.
    If the current time is before the cut off datetime, the current year's cut off datetime is returned.
    If the current time is after the cut off datetime, the next year's cut off datetime is returned.

    See TOKEN_CUT_OFF_DATETIME in settings for more information.
    """
    cut_off_time = settings.TOKEN_CUT_OFF_DATETIME

    now = timezone.now()
    token_cut_off_datetime = datetime.strptime(
        f"{now.year}-{cut_off_time}+0000", "%Y-%m-%d %H:%M%z"
    )
    if now > token_cut_off_datetime:
        token_cut_off_datetime = datetime.strptime(
            f"{now.year + 1}-{cut_off_time}+0000", "%Y-%m-%d %H:%M%z"
        )
    return token_cut_off_datetime
