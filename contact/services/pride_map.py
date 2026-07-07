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
        However, the fill and fill_opacity properties for the 'Omleiding' layer are not prefixed,
        as they are used for styling the layer and the geojson standard is used.
        """

        prefix = self.properties_prefix

        stroke, stroke_width = self._get_style_properties(
            layer_type=layer_type, geom=geom
        )
        title = self._get_title(properties)
        address = self._get_address(properties=properties, geom=geom)

        date_and_time = self._get_date_and_time(
            properties=properties, layer_type=layer_type
        )

        return {
            f"{prefix}title": title,
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}date_and_time": date_and_time,
            f"{prefix}website": self._get_website(properties),
            f"{prefix}address": address,
            f"{prefix}table": self._create_table(properties.get("meta", [])),
            "stroke": stroke,
            "stroke-width": stroke_width,
        }

    def _get_style_properties(
        self, *, layer_type: str, geom: Dict[str, Any]
    ) -> tuple[str | None, int | None]:
        if layer_type == "Canal parade" and geom.get("type") == "LineString":
            # for canal parade we want to add stroke and stroke-width properties
            return "#009DE6", 5

        return None, None

    @staticmethod
    def _get_title(properties: Dict[str, Any]) -> str:
        return properties.get("title", "")

    def _get_address(
        self, *, properties: Dict[str, Any], geom: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        if properties.get("street"):
            return self._get_address_from_properties(properties, geom)

        return None

    def _get_date_and_time(
        self, *, properties: Dict[str, Any], layer_type: str
    ) -> str | None:

        # first check if date is in the description
        date_and_time_from_description = self.get_date_and_time_from_description(
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
        if not any([start_date_str, end_date_str, start_time_str, end_time_str]):
            return None

        if start_date_str and end_date_str:
            # make one date string from start and end date
            if start_date_str == end_date_str:
                date_str = start_date_str
            else:
                date_str = f"{start_date_str} - {end_date_str}"

        elif start_date_str:
            date_str = start_date_str

        elif end_date_str:
            date_str = end_date_str

        if start_time_str and end_time_str:
            time_str = f"{start_time_str} tot {end_time_str}"
        elif start_time_str:
            time_str = f"vanaf {start_time_str}"
        elif end_time_str:
            time_str = f"tot {end_time_str}"
        else:
            time_str = None

        date_and_time = f"{date_str}"
        if time_str:
            date_and_time += f", {time_str}"

        return date_and_time

    def _get_date_and_time_strings(
        self, *, properties: Dict[str, Any], layer_type: str
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """
        Returns start and end date and time strings for a given data point based on the properties.
        """

        if layer_type == "Toilet":
            return self._get_date_and_time_for_toilets(properties)

        date_and_time_from_meta = self.get_date_and_time_from_meta(properties)
        if date_and_time_from_meta:
            return date_and_time_from_meta

        return None, None, None, None

    def _get_date_and_time_for_toilets(
        self, properties: Dict[str, Any]
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """
        Returns date and time for toilets based on the properties.
        """

        start_date_time = properties.get("date_start").split("T")
        start_time = (
            start_date_time[1].split("+")[0] if len(start_date_time) > 1 else None
        )
        start_date = start_date_time[0]

        end_date_time = properties.get("date_end").split("T")
        end_time = end_date_time[1].split("+")[0] if len(end_date_time) > 1 else None
        end_date = end_date_time[0]

        # format start and end date strings as Dutch localized dates, e.g. "za 1 aug 2026"
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        start_date_str = format_date(
            start_date_obj.date(), "EEE d MMM y", locale="nl_NL"
        )

        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        end_date_str = format_date(end_date_obj.date(), "EEE d MMM y", locale="nl_NL")

        # convert start and end time strings to different formats, for example 06:00:00 to 06:00
        start_time_str = start_time[:-3] if start_time else None
        end_time_str = end_time[:-3] if end_time else None

        return start_date_str, end_date_str, start_time_str, end_time_str

    def get_date_and_time_from_description(
        self, properties: Dict[str, Any]
    ) -> str | None:
        """
        Returns date and time for a given data point based on the properties.

        Example: description: "<p>za 1 aug 2026, 11:00 tot 15:00</p>" -> returns "za 1 aug 2026, 11:00 tot 15:00"
        """

        # check if description contains a date
        if properties.get("description"):
            description = self._clean_html(properties.get("description"))
            if re.search(r"\d{1,2} [a-zA-Z.]{3,}", description):
                return description

        else:
            return None

    def get_date_and_time_from_meta(self, properties: Dict[str, Any]) -> str | None:
        """
        Returns date and time for a given data point based on the meta properties.

        Example: meta: [{"key": "startdatum", "value": "2026-08-01"}, {"key": "einddatum", "value": "2026-08-02"}, {"key": "tijd", "value": "11:00-15:00"}] -> returns "za 1 aug 2026 - zo 2 aug 2026, 11:00 tot 15:00"
        """

        start_date = None
        end_date = None
        start_time = None
        end_time = None

        for meta in properties.get("meta", []):
            if meta.get("key") in ["startdatum", "datum-start"]:
                start_date = self._convert_date_string_to_iso_format(meta.get("value"))
            elif meta.get("key") in ["einddatum", "datum-eind", "datum-eind-tm"]:
                end_date = self._convert_date_string_to_iso_format(meta.get("value"))
            elif meta.get("key") in ["tijd"]:
                # check if time in format HH:MM-HH:MM, if so, add it to the start and end date
                if "-" in meta.get("value", ""):
                    splitted_time = meta.get("value").split("-")
                    if len(splitted_time) != 2:
                        logger.warning(
                            f"Unexpected time format: {meta.get('value')}. Expected format is HH:MM-HH:MM. Skipping time parsing."
                        )
                        continue
                    start_time = splitted_time[0].replace(".", ":").strip()
                    end_time = splitted_time[1].replace(".", ":").strip()
                else:
                    continue

        if not start_date and not end_date:
            return None

        # format start and end date strings as Dutch localized dates, e.g. "za 1 aug 2026"
        start_date_str = (
            format_date(
                datetime.strptime(start_date, "%Y-%m-%d").date(),
                "EEE d MMM y",
                locale="nl_NL",
            )
            if start_date
            else None
        )
        end_date_str = (
            format_date(
                datetime.strptime(end_date, "%Y-%m-%d").date(),
                "EEE d MMM y",
                locale="nl_NL",
            )
            if end_date
            else None
        )

        return start_date_str, end_date_str, start_time, end_time

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
                logger.warning(
                    f"Could not convert date string: {short_date}-{datetime.now().year}"
                )
                return None

            try:
                date_obj = date(
                    year=datetime.now().year,
                    month=month_number,
                    day=int(day_str),
                )
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                logger.warning(
                    f"Could not convert date string: {short_date}-{datetime.now().year}"
                )
                return None

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
