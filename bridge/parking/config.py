from typing import NamedTuple


class ReminderContent(NamedTuple):
    title: str
    body: str


REMINDER_MESSAGES = {
    "nl": ReminderContent(title="Herinnering", body="Uw parkeersessie loopt bijna af"),
    "en": ReminderContent(
        title="Reminder", body="Your parking session is about to end"
    ),
}

DEFAULT_LANGUAGE = "nl"
