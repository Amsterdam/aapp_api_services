from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    IconClass,
    ListPropertyClass,
)
from contact.icons import IconPath


class ChristmasTreeData(ChoicesEnum):
    CHRISTMAS_TREE = DataLayer(
        label="Inzamelpunten kerstbomen", code=44157, icon_label="christmas_tree"
    )


class ChristmasTreeFilters(ChoicesEnum):
    pass


class ChristmasTreeLayers(ChoicesEnum):
    pass
    # CHRISTMAS_TREE = LayerClass(
    #     label="Inzamelpunten kerstbomen",
    #     filter_key="aapp_subtitle",
    #     filter_value="Inzamelpunten kerstbomen",
    #     icon_label="christmas_tree",
    # )


class ChristmasTreeProperties(ChoicesEnum):
    pass


class ChristmasTreeSilentProperties(ChoicesEnum):
    pass


class ChristmasTreeIcons(ChoicesEnum):
    CHRISTMAS_TREE = IconClass(
        label="christmas_tree",
        path=IconPath["info"],
        circle_color="#E50082",
        path_color="#FFFFFF",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
