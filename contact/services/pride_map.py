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

    def _preprocess_feature(
        self, *, feature: Dict[str, Any], layer: Dict[str, Any]
    ) -> None:

        # if geometry is a multipoint, convert it to a point with the coordinates of the first point, as the frontend expects a point geometry for taps
        geom = feature.get("geometry", {}) or {}
        if (
            geom.get("type") == "MultiPoint"
            and isinstance(geom.get("coordinates"), list)
            and len(geom["coordinates"]) > 0
        ):
            feature["geometry"] = {
                "type": "Point",
                "coordinates": geom["coordinates"][0],
            }

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

        if layer_type == "Canal parade" and geom.get("type") == "LineString":
            # for canal parade we want to add stroke and stroke-width properties
            stroke = "#009DE6"
            stroke_width = 5
        else:
            stroke = None
            stroke_width = None

        title = properties.get("title", "")
        address = None
        if properties.get("street"):
            address = self._get_address_from_properties(properties, geom)

        date_properties = self._get_start_end_date_and_time(properties)

        if layer_type == "Toilet":
            date_and_time = self._get_date_and_time_for_toilets(properties)
        else:
            date_and_time = self.get_date_and_time_from_description(properties)

        return {
            f"{prefix}title": title,
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}date_and_time": date_and_time,
            f"{prefix}website": self._get_website(properties),
            f"{prefix}address": address,
            f"{prefix}table": self._create_table(properties.get("meta", [])),
            f"{prefix}start_date": date_properties.get("start_date"),
            f"{prefix}end_date": date_properties.get("end_date"),
            f"{prefix}start_time": date_properties.get("start_time"),
            f"{prefix}end_time": date_properties.get("end_time"),
            "stroke": stroke,
            "stroke-width": stroke_width,
        }

    def _get_date_and_time_for_toilets(self, properties: Dict[str, Any]) -> str | None:
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

        if start_date_str == end_date_str:
            date_str = start_date_str
        else:
            date_str = f"{start_date_str} - {end_date_str}"

        # convert start and end time strings to different formats, for example 06:00:00 to 06:00
        start_time_str = start_time[:-3] if start_time else None
        end_time_str = end_time[:-3] if end_time else None

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

    def _get_start_end_date_and_time(
        self, properties: Dict[str, Any]
    ) -> dict[str, str | None]:
        """
        Returns parsed start/end date and time values for a given data point.

        Dates are returned as 'YYYY-MM-DD' and times as 'HH:MM:SS' (timezone stripped when present).
        Missing values are returned as None.
        """

        date_time_properties = {
            "start_date": None,
            "end_date": None,
            "start_time": None,
            "end_time": None,
        }

        # for toilets, start and end date are stored in the properties directly, format "2026-08-01T06:00:00+02:00", so we need to split it
        if properties.get("date_start"):
            # split the date and time, and remove the timezone
            start_date_time = properties.get("date_start").split("T")
            start_time = (
                start_date_time[1].split("+")[0] if len(start_date_time) > 1 else None
            )

            date_time_properties["start_date"] = start_date_time[0]
            date_time_properties["start_time"] = start_time
        if properties.get("date_end"):
            end_date_time = properties.get("date_end").split("T")
            end_time = (
                end_date_time[1].split("+")[0] if len(end_date_time) > 1 else None
            )
            date_time_properties["end_date"] = end_date_time[0]
            date_time_properties["end_time"] = end_time

        # for other layers, the start and end date are stored in the meta property
        # also they can be in different formats, so we need to convert them to one format (YYYY-MM-DD)
        for meta in properties.get("meta", []):
            if meta.get("key") in ["startdatum", "datum-start"]:
                date_time_properties["start_date"] = (
                    self._convert_date_string_to_iso_format(meta.get("value"))
                )
            elif meta.get("key") in ["einddatum", "datum-eind", "datum-eind-tm"]:
                date_time_properties["end_date"] = (
                    self._convert_date_string_to_iso_format(meta.get("value"))
                )
            elif meta.get("key") in ["tijd"]:
                # check if time in format HH:MM-HH:MM, if so, add it to the start and end date
                if "-" in meta.get("value", ""):
                    splitted_time = meta.get("value").split("-")
                    if len(splitted_time) != 2:
                        logger.warning(
                            f"Unexpected time format: {meta.get('value')}. Expected format is HH:MM-HH:MM. Skipping time parsing."
                        )
                        continue
                    date_time_properties["start_time"] = (
                        splitted_time[0].replace(".", ":").strip()
                    )
                    date_time_properties["end_time"] = (
                        splitted_time[1].replace(".", ":").strip()
                    )
                else:
                    continue

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
