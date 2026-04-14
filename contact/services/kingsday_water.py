from contact.enums.kingsday_water import (
    LIST_PROPERTY,
    KingsdayWaterData,
    KingsdayWaterFilters,
    KingsdayWaterIcons,
    KingsdayWaterLayers,
    KingsdayWaterProperties,
)
from contact.services.kingsday_abstract import KingsdayAbstractService


class KingsdayWaterService(KingsdayAbstractService):
    data_enum = KingsdayWaterData
    filters_enum = KingsdayWaterFilters
    layers_enum = KingsdayWaterLayers
    properties_enum = KingsdayWaterProperties
    icons_enum = KingsdayWaterIcons
    list_property = LIST_PROPERTY
