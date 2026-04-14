from contact.enums.base import ChoicesEnum, DataLayer, FilterClass, IconClass
from contact.icons import IconPath


class KingsdayWaterData(ChoicesEnum):
    BOATING_BAN = DataLayer(label="Invaarverbod", code=44258, icon_label="boating_ban")


class KingsdayWaterFilters(ChoicesEnum):
    pass


class KingsdayWaterLayers(ChoicesEnum):
    BOATING_BAN = FilterClass(
        label="Invaarverbod", filter_key="aapp_subtitle", filter_value="Invaarverbod"
    )


class KingsdayWaterProperties(ChoicesEnum):
    pass


class KingsdayWaterIcons(ChoicesEnum):
    BOATING_BAN = IconClass(
        label="boating_ban",
        path=IconPath["tap-tap-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
