from collections import defaultdict

from waste import constants
from waste.constants import WASTE_TYPES_ORDER
from waste.services.waste_collection_abstract import WasteCollectionAbstractService


class WasteCollectionService(WasteCollectionAbstractService):
    def __init__(self, bag_nummeraanduiding_id: str):
        super().__init__(bag_nummeraanduiding_id)

    def create_calendar(self):
        calendar = []
        for item in self.validated_data:
            if item.get("basisroutetypeCode") not in ["BIJREST", "GROFAFSPR"]:
                dates = self.get_dates_for_waste_item(item)
                calendar += [
                    {
                        "date": date,
                        **{
                            k: item.get(k)
                            for k in [
                                "label",
                                "code",
                                "curb_rules_from",
                                "curb_rules_to",
                                "alert",
                            ]
                        },
                    }
                    for date in dates
                ]
        # sort calendar items by date
        calendar.sort(key=lambda x: x["date"])
        return calendar

    def get_next_dates(self, calendar):
        dates = defaultdict(list)
        for item in calendar:
            code = item.get("code")
            dates[code].append(item["date"])

        next_dates = {code: None for code in WASTE_TYPES_ORDER}
        for code in next_dates:
            next_dates[code] = min(dates[code]) if dates[code] else None

        return next_dates

    def get_waste_types(self, next_dates):
        waste_types = []
        for item in self.validated_data:
            code = item.get("code")
            if code in constants.WASTE_TYPES_ORDER:
                waste_types.append(
                    {
                        **{
                            k: item.get(k)
                            for k in [
                                "label",
                                "code",
                                "curb_rules",
                                "alert",
                                "note",
                                "days_array",
                                "how",
                                "where",
                                "button_text",
                                "url",
                                "frequency",
                                "is_collection_by_appointment",
                            ]
                        },
                        "next_date": next_dates.get(code),
                        "info_link": self.waste_links.get(code),
                    }
                )
        waste_types.sort(
            key=lambda x: (
                WASTE_TYPES_ORDER.index(x["code"])
                if x["code"] in WASTE_TYPES_ORDER
                else 999
            )
        )
        return waste_types

    def get_is_residential(self):
        if self.validated_data and len(self.validated_data) > 0:
            return self.validated_data[0].get("is_residential")
        return True

    def get_is_collection_by_appointment(self):
        for item in self.validated_data:
            if item.get("code") == "Rest":
                return item.get("is_collection_by_appointment")
        return False
