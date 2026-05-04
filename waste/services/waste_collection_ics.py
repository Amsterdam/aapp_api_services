from waste.services.waste_collection_abstract import WasteCollectionAbstractService
from waste.services.waste_ics import WasteICS


class WasteCollectionICSService(WasteCollectionAbstractService):
    def create_ics_calendar(self, validated_data) -> str:
        waste_calendar = WasteICS()
        for item in validated_data:
            if item.get("basisroutetypeCode") in ["BIJREST", "GROFAFSPR"]:
                continue

            dates = self.get_dates_for_waste_item(item)
            for date in dates:
                waste_calendar.add_event_to_calendar(date, item)

        waste_calendar.add_calendar_ending()

        return waste_calendar.calendar
