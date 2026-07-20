import logging
import re
from datetime import date, datetime
from typing import Any, Dict

from babel.dates import format_date, get_month_names

from contact.enums.pride_map import (
    LIST_PROPERTY,
    PrideMapData,
    PrideMapFilters,
    PrideMapIcons,
    PrideMapLayers,
    PrideMapProperties,
    PrideMapSilentProperties,
)
from contact.services.event_abstract import EventAbstractService

logger = logging.getLogger(__name__)


class PrideMapService(EventAbstractService):
    TOILET_LAYER = "Toilet"
    DUTCH_DATE_FORMAT = "EEE d MMM y"
    ISO_DATE_FORMAT = "%Y-%m-%d"

    data_enum = PrideMapData
    filters_enum = PrideMapFilters
    layers_enum = PrideMapLayers
    properties_enum = PrideMapProperties
    silent_properties_enum = PrideMapSilentProperties
    icons_enum = PrideMapIcons
    list_property = LIST_PROPERTY

    def get_custom_properties(
        self,
        properties: Dict[str, Any],
        geom: Dict[str, Any],
        layer_type: str,
        icon_name: str | None,
    ) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a given data point,
        based on the original properties, geometry, layer type, and icon name.

        All custom properties are prefixed with 'aapp_' to avoid conflicts with original properties.
        However, the stroke and stroke-width properties are not prefixed,
        as they are used for styling the layer and the geojson standard is used.
        """

        prefix = self.properties_prefix

        stroke, stroke_width = self._get_style_properties(
            layer_type=layer_type, geom=geom
        )
        title = properties.get("title", "")

        address = None
        if properties.get("street"):
            address = self._get_address_from_properties(properties, geom)

        date_and_time = self._get_date_and_time(
            properties=properties, layer_type=layer_type
        )

        if layer_type == "Toilet":
            table = self._create_table(properties.get("meta", []))
        else:
            table = None

        description = None
        if layer_type == "EHBO-post":
            description = properties.get("description", "")

        return {
            f"{prefix}title": title,
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}date_and_time": date_and_time,
            f"{prefix}website": self._get_website(properties),
            f"{prefix}address": address,
            f"{prefix}table": table,
            f"{prefix}description": description,
            "stroke": stroke,
            "stroke-width": stroke_width,
        }

    def _get_style_properties(
        self, *, layer_type: str, geom: Dict[str, Any]
    ) -> tuple[str | None, int | None]:
        if layer_type == "Canal parade" and geom.get("type") == "LineString":
            # for canal parade we want to add stroke and stroke-width properties
            stroke = "#009DE6"
            stroke_width = 5
        elif layer_type == "Pride walk" and geom.get("type") == "LineString":
            # for pride walk we want to add stroke and stroke-width properties
            stroke = "#A00078"
            stroke_width = 5
        elif layer_type == "Pride march" and geom.get("type") == "LineString":
            # for pride march we want to add stroke and stroke-width properties
            stroke = "#F52FD0"
            stroke_width = 5
        else:
            stroke = None
            stroke_width = None

        return stroke, stroke_width

    def _get_date_and_time(
        self, *, properties: Dict[str, Any], layer_type: str
    ) -> str | None:
        # first check if date is in the description
        date_and_time_from_description = self._get_date_and_time_from_description(
            properties=properties
        )
        if date_and_time_from_description:
            return date_and_time_from_description

        start_date_str, end_date_str, start_time_str, end_time_str = (
            self._get_date_and_time_strings(
                properties=properties, layer_type=layer_type
            )
        )

        # if all fields are None, return None
        if not any((start_date_str, end_date_str, start_time_str, end_time_str)):
            return None

        date_str = self._build_date_range(start_date_str, end_date_str)
        time_str = self._build_time_range(start_time_str, end_time_str)

        date_and_time = date_str
        if time_str:
            date_and_time += f", {time_str}"

        return date_and_time

    def _get_date_and_time_strings(
        self, *, properties: Dict[str, Any], layer_type: str
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """
        Returns start and end date and time strings for a given data point based on the properties.
        """

        if layer_type == self.TOILET_LAYER:
            return self._get_date_and_time_for_toilets(properties)

        date_and_time_from_meta = self._get_date_and_time_from_meta(properties)
        if date_and_time_from_meta:
            return date_and_time_from_meta

        return None, None, None, None

    def _get_date_and_time_for_toilets(
        self, properties: Dict[str, Any]
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """
        Returns date and time for toilets based on the properties.
        """

        start_date, start_time = self._split_datetime(properties.get("date_start"))
        end_date, end_time = self._split_datetime(properties.get("date_end"))

        start_date_str = self._format_dutch_date(start_date)
        end_date_str = self._format_dutch_date(end_date)
        start_time_str = self._truncate_seconds(start_time)
        end_time_str = self._truncate_seconds(end_time)

        return start_date_str, end_date_str, start_time_str, end_time_str

    def _get_date_and_time_from_description(
        self, properties: Dict[str, Any]
    ) -> str | None:
        """
        Returns date and time for a given data point based on the properties.

        Example: description: "<p>za 1 aug 2026, 11:00 tot 15:00</p>" -> returns "za 1 aug 2026, 11:00 tot 15:00"
        """

        description_html = properties.get("description")
        if not description_html:
            return None

        description = self._clean_html(description_html)
        if re.search(r"\d{1,2} [a-zA-Z.]{3,} \d{4}", description):
            return description

        return None

    def _get_date_and_time_from_meta(
        self, properties: Dict[str, Any]
    ) -> tuple[str | None, str | None, str | None, str | None] | None:
        """
        Returns date and time for a given data point based on the meta properties.

        Example: meta: [{"key": "startdatum", "value": "2026-08-01"}, {"key": "einddatum", "value": "2026-08-02"}, {"key": "tijd", "value": "11:00-15:00"}] -> returns "za 1 aug 2026 - zo 2 aug 2026, 11:00 tot 15:00"
        """

        date_time_properties = self._get_start_end_date_and_time_properties_from_meta(
            properties=properties
        )

        start_date_str = self._format_dutch_date(date_time_properties["start_date"])
        end_date_str = self._format_dutch_date(date_time_properties["end_date"])

        return (
            start_date_str,
            end_date_str,
            date_time_properties["start_time"],
            date_time_properties["end_time"],
        )

    def _get_start_end_date_and_time_properties_from_meta(
        self, properties: Dict[str, Any]
    ) -> tuple[str | None, str | None, str | None, str | None]:

        date_time_properties = {
            "start_date": None,
            "end_date": None,
            "start_time": None,
            "end_time": None,
        }

        for meta in properties.get("meta", []):
            if meta.get("key") in ["startdatum", "datum-start"]:
                date_time_properties["start_date"] = (
                    self._convert_date_string_to_iso_format(meta.get("value"))
                )
            elif meta.get("key") in ["einddatum", "datum-eind", "datum-eind-tm"]:
                date_time_properties["end_date"] = (
                    self._convert_date_string_to_iso_format(meta.get("value"))
                )
            elif meta.get("key") == "tijd":
                # check if time in format HH:MM-HH:MM, if so, add it to the start and end date
                parsed_time_range = self._parse_time_range(meta.get("value"))
                if not parsed_time_range:
                    continue
                date_time_properties["start_time"], date_time_properties["end_time"] = (
                    parsed_time_range
                )

        return date_time_properties

    def _convert_date_string_to_iso_format(self, date_string: str | None) -> str | None:
        """
        Converts a date string to 'YYYY-MM-DD'.

        Expected input formats:
        - 8-jul -> important!! current year is assumed, so if the current year is 2026, the output will be 2026-07-08
        - YYYY-MM-DD
        - YYYY-MM-DDgarbage
        If the input is not in the expected format, returns None and log other format.
        """
        if not date_string:
            return None

        # use regex to check if the string contains a date in the format 'YYYY-MM-DD', if so, return it
        match = re.search(r"\d{4}-\d{2}-\d{2}", date_string)
        if match:
            return match.group(0)

        # check if the string contains a date in the format 'DD-MMM', if so, convert it to 'YYYY-MM-DD' using the current year
        # for example, 8-jul -> 2026-07-08
        match = re.search(r"\d{1,2}-[a-zA-Z.]{3,}", date_string)
        if match:
            short_date = match.group(0)
            day_str, month_name = short_date.split("-", maxsplit=1)
            month_number = self._get_month_number_from_name(month_name)
            if not month_number:
                logger.warning(f"Could not convert date string: {date_string}")
                return None
            year = datetime.now().year
            if int(month_number) < 6:
                year += 1

            try:
                date_obj = date(
                    year=year,
                    month=month_number,
                    day=int(day_str),
                )
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                logger.warning(f"Could not convert date string: {date_string}")
                return None

        return None

    @staticmethod
    def _build_date_range(start_date: str | None, end_date: str | None) -> str:
        if start_date and end_date:
            return (
                start_date if start_date == end_date else f"{start_date} - {end_date}"
            )
        return start_date or end_date or ""

    @staticmethod
    def _build_time_range(start_time: str | None, end_time: str | None) -> str | None:
        if start_time and end_time:
            return f"{start_time} tot {end_time}"
        if start_time:
            return f"vanaf {start_time}"
        if end_time:
            return f"tot {end_time}"
        return None

    @staticmethod
    def _split_datetime(value: str | None) -> tuple[str | None, str | None]:
        if not value:
            return None, None

        date_time_parts = value.split("T")
        date_part = date_time_parts[0]
        if len(date_time_parts) == 1:
            return date_part, None

        time_part = date_time_parts[1].split("+")[0]
        return date_part, time_part

    @staticmethod
    def _truncate_seconds(value: str | None) -> str | None:
        # Converts values like 06:00:00 to 06:00 for display.
        if not value:
            return None

        splitted_value = value.split(":")
        if len(splitted_value) >= 2:
            return ":".join(splitted_value[:2])
        return value

    def _format_dutch_date(self, iso_date: str | None) -> str | None:
        if not iso_date:
            return None

        return format_date(
            datetime.strptime(iso_date, self.ISO_DATE_FORMAT).date(),
            self.DUTCH_DATE_FORMAT,
            locale="nl_NL",
        )

    def _parse_time_range(self, value: str | None) -> tuple[str, str] | None:
        if not value or "-" not in value:
            return None

        split_time = value.split("-")
        if len(split_time) != 2:
            logger.warning(
                f"Unexpected time format: {value}. Expected format is HH:MM-HH:MM. Skipping time parsing."
            )
            return None

        start_time = split_time[0].replace(".", ":").strip()
        end_time = split_time[1].replace(".", ":").strip()
        return start_time, end_time

    @staticmethod
    def _get_month_number_from_name(month_name: str) -> int | None:
        normalized_month = month_name.strip().lower().rstrip(".")

        month_names = get_month_names(width="abbreviated", locale="nl_NL")
        for month_number, localized_month_name in month_names.items():
            if not localized_month_name:
                continue
            if localized_month_name.strip().lower().rstrip(".") == normalized_month:
                return month_number
        return None
