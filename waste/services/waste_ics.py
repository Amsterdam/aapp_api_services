from datetime import date, datetime, time, timedelta

from django.utils import timezone

from waste.constants import WASTE_TYPES_MAPPING_READABLE

CALENDAR_START = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//Amsterdam App//Afvalwijzer kalender//NL\r\n"
    "CALSCALE:GREGORIAN\r\n"
    "METHOD:PUBLISH\r\n"
    "SUMMARY:Afvalwijzer Gemeente Amsterdam\r\n"
    "X-WR-CALNAME:Afvalwijzer kalender\r\n"
    "X-WR-TIMEZONE:Europe/Amsterdam\r\n"
    "BEGIN:VTIMEZONE\r\n"
    "TZID:Europe/Amsterdam\r\n"
    "X-LIC-LOCATION:Europe/Amsterdam\r\n"
    "BEGIN:DAYLIGHT\r\n"
    "TZOFFSETFROM:+0100\r\n"
    "TZOFFSETTO:+0200\r\n"
    "TZNAME:GMT+2\r\n"
    "DTSTART:19700329T020000\r\n"
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU\r\n"
    "END:DAYLIGHT\r\n"
    "BEGIN:STANDARD\r\n"
    "TZOFFSETFROM:+0200\r\n"
    "TZOFFSETTO:+0100\r\n"
    "TZNAME:GMT+1\r\n"
    "DTSTART:19701025T030000\r\n"
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU\r\n"
    "END:STANDARD\r\n"
    "END:VTIMEZONE\r\n"
)

EVENT_TEMPLATE = (
    "BEGIN:VEVENT\r\n"
    "UID:{uid}\r\n"
    "DTSTAMP:{dtstamp}\r\n"
    "SUMMARY:{summary}\r\n"
    "DESCRIPTION:{description}\r\n"
    "DTSTART;TZID=Europe/Amsterdam:{dtstart}\r\n"
    "DTEND;TZID=Europe/Amsterdam:{dtend}\r\n"
    "END:VEVENT\r\n"
)


class WasteICS:
    def __init__(self):
        self.calendar = CALENDAR_START

    def add_event_to_calendar(self, event_date, item):
        event = self._create_ics_event(event_date, item)
        self.calendar += event

    @staticmethod
    def _create_ics_event(event_date: date, item: dict) -> str:
        readable_name = WASTE_TYPES_MAPPING_READABLE.get(item.get("code")) or "Afval"
        event_uid = f"{readable_name.replace(',', '').replace(' ', '')}-{event_date.isoformat()}@app.amsterdam.nl"
        event_name = f"Ophaaldag {readable_name.lower()}"

        # start of day timestamp
        created_timestamp = timezone.make_aware(
            datetime.combine(date.today(), time.min), timezone.get_current_timezone()
        )
        created_timestamp_str = created_timestamp.strftime("%Y%m%dT%H%M%SZ")

        # set description
        event_description = ""
        if item.get("curb_rules_from") and item.get("curb_rules_to"):
            event_description += f"Buiten zetten: {item.get('curb_rules_from', '')} {item.get('curb_rules_to', '')}"

        event_start = event_date.strftime("%Y%m%d")
        event_end = (event_date + timedelta(days=1)).strftime("%Y%m%d")

        event_string = EVENT_TEMPLATE.format(
            uid=event_uid,
            dtstamp=created_timestamp_str,
            summary=event_name,
            description=event_description,
            dtstart=event_start,
            dtend=event_end,
        )

        return event_string

    def add_calendar_ending(self):
        self.calendar += "END:VCALENDAR"
