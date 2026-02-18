from collections import OrderedDict
from datetime import date

from fpdf import FPDF

from waste.constants import WASTE_TYPES_MAPPING_READABLE
from waste.services.waste_collection_abstract import WasteCollectionAbstractService
from waste.services.waste_pdf import (
    WastePDF,
)


class WasteCollectionPDFService(WasteCollectionAbstractService):
    def __init__(self, bag_nummeraanduiding_id: str):
        super().__init__(bag_nummeraanduiding_id)

    def get_pdf_calendar(self) -> FPDF:
        # get all necessary data
        waste_collection_by_date = self.create_pdf_calendar_dates()
        days = self.all_dates
        months = self.group_days_by_month(days)

        # initialize pdf and get settings
        pdf = WastePDF(address=self._generate_address_string())
        pdf.add_page()
        pdf.add_title()

        # draw months
        for (year, month), month_days in months.items():
            needed_height = pdf.estimate_month_height(year, month, month_days)
            if pdf.remaining_page_height() < needed_height:
                pdf.add_page()
            pdf.draw_pdf_month(year, month, month_days, waste_collection_by_date)

        return pdf

    def create_pdf_calendar_dates(self) -> dict[date, list[str]]:
        waste_collection_by_date = {}
        for item in self.validated_data:
            if item.get("basisroutetypeCode") not in ["BIJREST", "GROFAFSPR"]:
                dates = self.get_dates_for_waste_item(item)
                for date in dates:
                    waste_collection_by_date.setdefault(date, []).append(
                        WASTE_TYPES_MAPPING_READABLE.get(item.get("code"))
                    )

        return waste_collection_by_date

    @staticmethod
    def group_days_by_month(days: list[date]) -> OrderedDict:
        months = OrderedDict()
        for d in days:
            key = (d.year, d.month)
            months.setdefault(key, []).append(d)
        return months

    def _generate_address_string(self) -> str:
        if not self.validated_data or len(self.validated_data) == 0:
            return ""
        first_item = self.validated_data[0]
        street_name = first_item.get("street_name", "")
        house_number = first_item.get("house_number", "")
        house_letter = first_item.get("house_letter", "")
        house_number_addition = first_item.get("house_number_addition", "")
        postal_code = first_item.get("postal_code", "")
        city_name = first_item.get("city_name", "")

        address_parts = [street_name, house_number]
        if house_letter:
            address_parts.append(house_letter)
        if house_number_addition:
            address_parts.append(house_number_addition)
        address = " ".join(address_parts)
        if postal_code:
            address += f", {postal_code}"
        if city_name:
            address += f" {city_name}"

        return address.strip()
