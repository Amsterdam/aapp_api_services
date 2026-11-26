from collections import defaultdict
from datetime import date

from waste import constants
from waste.constants import WASTE_TYPES_CODES
from waste.services.waste_collection_abstract import WasteCollectionAbstractService


class WasteCollectionService(WasteCollectionAbstractService):
    def create_calendar(self, validated_data) -> list[dict]:
        calendar = []
        for item in validated_data:
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

    def get_next_dates(self, calendar: list[dict]) -> dict[str, str | None]:
        dates = defaultdict(list)
        for item in calendar:
            code = item.get("code")
            dates[code].append(item["date"])

        next_dates = {code: None for code in WASTE_TYPES_CODES}
        for code in next_dates:
            next_dates[code] = min(dates[code]) if dates[code] else None

        return next_dates

    def get_waste_types(
        self, validated_data, next_dates: dict[str, str | None]
    ) -> list[dict]:
        waste_types = []
        for item in validated_data:
            code = item.get("code")
            if code in constants.WASTE_TYPES_CODES:
                waste_types.append(
                    {
                        **{
                            k: item.get(k)
                            for k in [
                                "label",
                                "code",
                                "order",
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

        sorted_waste_types = self.sort_waste_types_by_order(waste_types)
        today = date.today()
        if self._is_kerstbomen_season(today):
            sorted_waste_types.append(self._get_kerstbomen_waste_type(today))

        return sorted_waste_types

    @staticmethod
    def _is_kerstbomen_season(today: date) -> bool:
        return (today.month == 12 and today.day >= 14) or (
            today.month == 1 and today.day <= 17
        )

    @staticmethod
    def _get_kerstbomen_waste_type(today: date) -> dict:
        item = {
            "label": "Kerstbomen",
            "code": "Kerstbomen",
            "curb_rules": "28 december tot en met 17 januari",
            "alert": (
                "31 december en 1 januari geen kerstbomen plaatsen."
                if today.month == 12 or today.day == 1
                else None
            ),
            "note": "<p><b>Waar moet u op letten:</b> Kerstboom schoon, zonder versiering, lampjes en pot.<br><br><b>Eerder of later inleveren:</b> Breng deze naar een recyclepunt.</p><p><b>Kunstkerstbomen:</b> Breng deze naar de kringloop, een recyclepunt of bij het grof afval.</p>",
            "days_array": [],
            "how": None,
            "where": "",
            "button_text": None,
            "url": None,
            "frequency": None,
            "next_date": None,
            "info_link": None,
        }
        if today.month == 1 or today.day >= 28:
            item["sublabel"] = "Inleveren tot 17 januari"
        return item

    def sort_waste_types_by_order(self, waste_types: list[dict]) -> list[dict]:
        return sorted(
            waste_types,
            key=lambda x: x.get("order") if x.get("order") is not None else 999,
        )

    def get_is_residential(self, validated_data):
        if validated_data and len(validated_data) > 0:
            return validated_data[0].get("is_residential")
        return True

    def get_is_collection_by_appointment(self, validated_data):
        for item in validated_data:
            if item.get("code") == "Rest":
                return item.get("is_collection_by_appointment")
        return False
