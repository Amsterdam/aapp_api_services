from datetime import date

from django.test import TestCase

from waste.services.waste_ics import WasteICS


class WasteICSServiceTest(TestCase):
    def test_ics_calendar_creation(self):
        calendar = WasteICS()
        self.assertIn("BEGIN:VCALENDAR", calendar.calendar)

    def test_add_event_to_calendar(self):
        calendar = WasteICS()
        calendar.add_event_to_calendar(date(2026, 1, 12), {"code": "Rest"})
        self.assertIn("BEGIN:VEVENT", calendar.calendar)
        self.assertIn("DTSTART;TZID=Europe/Amsterdam:20260112", calendar.calendar)
        self.assertIn("END:VEVENT", calendar.calendar)

    def test_add_calendar_ending(self):
        calendar = WasteICS()
        calendar.add_calendar_ending()
        self.assertIn("END:VCALENDAR", calendar.calendar)
