from typing import NamedTuple


class ReminderContent(NamedTuple):
    title: str
    body: str


REMINDER_MESSAGES = {
    "nl": ReminderContent(
        title="Parkeeractie herinnering", body="Uw parkeersessie eindigt binnenkort"
    ),
    "en": ReminderContent(
        title="Parking session reminder", body="Your parking session is about to end"
    ),
}

DEFAULT_LANGUAGE = "nl"
