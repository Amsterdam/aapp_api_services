import re

import freezegun
import responses
from django.conf import settings
from django.test import override_settings

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.services.waste_collection_ics import WasteCollectionICSService
from waste.tests.mock_data import (
    frequency_monthly,
)


@freezegun.freeze_time("2025-12-09")
class WasteCollectionICSServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = WasteCollectionICSService(bag_nummeraanduiding_id="1234")
        responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"),
            json=frequency_monthly.MOCK_DATA,
        )
        self.service.get_validated_data()

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_ics_calendar(self):
        calendar = self.service.create_ics_calendar()

        # make sure calendar has a start and an end
        self.assertIn("BEGIN:VCALENDAR", str(calendar))
        self.assertIn("END:VCALENDAR", str(calendar))

        self.assertIn("BEGIN:VEVENT", str(calendar))
        self.assertIn("DTSTART;TZID=Europe/Amsterdam:20260112", str(calendar))
        # PRODID and DTSTAMP are required for iCalendar standard
        self.assertIn("PRODID", str(calendar))
        self.assertIn("DTSTAMP", str(calendar))
        # SCALE and METHOD are required for Google Calendar standard
        self.assertIn("CALSCALE:GREGORIAN", str(calendar))
        self.assertIn("METHOD:PUBLISH", str(calendar))
