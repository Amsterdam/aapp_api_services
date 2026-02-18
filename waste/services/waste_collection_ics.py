from waste.services.waste_collection_abstract import WasteCollectionAbstractService
from waste.services.waste_ics import WasteICS


class WasteCollectionICSService(WasteCollectionAbstractService):
    def __init__(self, bag_nummeraanduiding_id: str):
        super().__init__(bag_nummeraanduiding_id)

    def create_ics_calendar(self) -> str:
        waste_calendar = WasteICS()
        for item in self.validated_data:
            if item.get("basisroutetypeCode") not in ["BIJREST", "GROFAFSPR"]:
                dates = self.get_dates_for_waste_item(item)
                for date in dates:
                    waste_calendar.add_event_to_calendar(date, item)

        waste_calendar.add_calendar_ending()

        return waste_calendar.calendar
