from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    IconClass,
    LayerClass,
    ListPropertyClass,
    PropertiesClass,
)
from contact.icons import IconPath


class PrideMapData(ChoicesEnum):
    CANAL_PARADE = DataLayer(
        label="Canal parade", code=44334, icon_label="canal_parade"
    )
    # EVENTS = DataLayer(label="Evenement", code=44337, icon_label="event") # maybe later added again
    PRIDE_WALK = DataLayer(label="Pride walk", code=44331, icon_label="pride_walk")
    PRIDE_MARCH = DataLayer(label="Pride march", code=44340, icon_label="pride_march")
    TOILET = DataLayer(label="Toilet", code=44319, icon_label="toilet")
    CLOSURE = DataLayer(label="Afsluiting", code=44322, icon_label="closure")
    WATER_OBSTRUCTION = DataLayer(
        label="Waterstremming", code=44325, icon_label="water_obstruction"
    )


class PrideMapFilters(ChoicesEnum):
    pass


class PrideMapLayers(ChoicesEnum):
    CANAL_PARADE = LayerClass(
        label="Canal parade",
        filter_key="aapp_subtitle",
        filter_value="Canal parade",
        icon_label="canal_parade",
    )
    # EVENT = LayerClass(
    #     label="Evenement",
    #     filter_key="aapp_subtitle",
    #     filter_value="Evenement",
    #     icon_label="event",
    # )
    PRIDE_WALK = LayerClass(
        label="Pride walk",
        filter_key="aapp_subtitle",
        filter_value="Pride walk",
        icon_label="pride_walk",
    )
    PRIDE_MARCH = LayerClass(
        label="Pride march",
        filter_key="aapp_subtitle",
        filter_value="Pride march",
        icon_label="pride_march",
    )
    TOILET = LayerClass(
        label="Toilet",
        filter_key="aapp_subtitle",
        filter_value="Toilet",
        icon_label="toilet",
    )
    CLOSURE = LayerClass(
        label="Afsluiting",
        filter_key="aapp_subtitle",
        filter_value="Afsluiting",
        icon_label="closure",
    )
    WATER_OBSTRUCTION = LayerClass(
        label="Waterstremming",
        filter_key="aapp_subtitle",
        filter_value="Waterstremming",
        icon_label="water_obstruction",
    )


class PrideMapProperties(ChoicesEnum):
    WHEN = PropertiesClass(
        label="Wanneer",
        property_key="aapp_date_and_time",
        property_type="string",
        icon=IconPath["clock"],
    )
    ADDRESS = PropertiesClass(
        label="Adres",
        property_key="aapp_address",
        property_type="address",
        icon=IconPath["map-marker"],
    )
    TABLE = PropertiesClass(
        label="Overige informatie",
        property_key="aapp_table",
        property_type="key_value_table",
        icon=None,
    )
    WEBSITE = PropertiesClass(
        label=None,
        property_key="aapp_website",
        property_type="url",
        icon=None,
    )


class PrideMapSilentProperties(ChoicesEnum):
    STROKE = PropertiesClass(
        label=None,
        property_key="stroke",
        property_type="string",
        icon=None,
    )
    STROKE_WIDTH = PropertiesClass(
        label=None,
        property_key="stroke-width",
        property_type="integer",
        icon=None,
    )


class PrideMapIcons(ChoicesEnum):
    CANAL_PARADE = IconClass(
        label="canal_parade",
        path=IconPath["pride-canal-parade"],
        circle_color="#E50082",
        path_color="#FFFFFF",
    )
    # EVENT = IconClass(
    #     label="event",
    #     path=IconPath["pride-event"],
    #     circle_color="#FF9100",
    #     path_color="#181818",
    # )
    PRIDE_WALK = IconClass(
        label="pride_walk",
        path=IconPath["pride-walk"],
        circle_color="#A00078",
        path_color="#FFFFFF",
    )
    PRIDE_MARCH = IconClass(
        label="pride_march",
        path=IconPath["pride-march"],
        circle_color="#F52FD0",
        path_color="#FFFFFF",
    )
    TOILET = IconClass(
        label="toilet",
        path=IconPath["pride-toilet"],
        circle_color="#00A03C",
        path_color="#FFFFFF",
    )
    CLOSURE = IconClass(
        label="closure",
        path=IconPath["circle"],
        circle_color="#FFE600",
        path_color="#181818",
    )
    WATER_OBSTRUCTION = IconClass(
        label="water_obstruction",
        path=IconPath["pride-water-obstruction"],
        circle_color="#FF9100",
        path_color="#181818",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
