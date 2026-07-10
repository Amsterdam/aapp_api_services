from contact.enums.base import (
    ChoicesEnum,
    IconClass,
    LayerClass,
    ListPropertyClass,
)
from contact.icons import IconPath


class SwimmingSpotFilter(ChoicesEnum):
    pass


class SwimmingSpotProperties(ChoicesEnum):
    pass


class SwimmingSpotLayers(ChoicesEnum):
    INDOOR_POOL = LayerClass(
        label="Binnenzwembad",
        filter_key="aapp_subtitle",
        filter_value="Binnenzwembad",
        icon_label="indoor_pool",
    )
    OUTDOOR_POOL = LayerClass(
        label="Buitenzwembad",
        filter_key="aapp_subtitle",
        filter_value="Buitenzwembad",
        icon_label="outdoor_pool",
    )
    OUTDOOR_SPOT = LayerClass(
        label="Officiële buitenzwemplek",
        filter_key="aapp_subtitle",
        filter_value="Officiële buitenzwemplek",
        icon_label="outdoor_spot",
    )
    KIDS_POOL = LayerClass(
        label="Peuterbadje",
        filter_key="aapp_subtitle",
        filter_value="Peuterbadje",
        icon_label="kids_pool",
    )
    WATER_PARK = LayerClass(
        label="Waterspeeltuin",
        filter_key="aapp_subtitle",
        filter_value="Waterspeeltuin",
        icon_label="water_park",
    )


class SwimmingSpotIcons(ChoicesEnum):
    INDOOR_POOL = IconClass(
        label="indoor_pool",
        path=IconPath["swimming-indoor-pool"],
        circle_color="#004699",
        path_color="#FFFFFF",
    )
    OUTDOOR_POOL = IconClass(
        label="outdoor_pool",
        path=IconPath["swimming-outdoor-pool"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    OUTDOOR_SPOT = IconClass(
        label="outdoor_spot",
        path=IconPath["swimming-outdoor-spot"],
        circle_color="#00A03C",
        path_color="#FFFFFF",
    )
    KIDS_POOL = IconClass(
        label="kids_pool",
        path=IconPath["swimming-kids-pool"],
        circle_color="#FFE600",
        path_color="#181818",
    )
    WATER_PARK = IconClass(
        label="water_park",
        path=IconPath["swimming-water-park"],
        circle_color="#E50082",
        path_color="#FFFFFF",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
