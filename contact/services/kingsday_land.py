from contact.enums.kingsday_land import (
    LIST_PROPERTY,
    KingsdayLandData,
    KingsdayLandFilters,
    KingsdayLandIcons,
    KingsdayLandLayers,
    KingsdayLandProperties,
)
from contact.services.kingsday_abstract import KingsdayAbstractService


class KingsdayLandService(KingsdayAbstractService):
    data_enum = KingsdayLandData
    filters_enum = KingsdayLandFilters
    layers_enum = KingsdayLandLayers
    properties_enum = KingsdayLandProperties
    icons_enum = KingsdayLandIcons
    list_property = LIST_PROPERTY
