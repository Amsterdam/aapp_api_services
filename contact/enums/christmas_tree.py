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


class ChristmasTreeProperties(ChoicesEnum):
    pass


class ChristmasTreeSilentProperties(ChoicesEnum):
    pass


class ChristmasTreeIcons(ChoicesEnum):
    CHRISTMAS_TREE = IconClass(
        label="christmas_tree",
        path=IconPath["christmas-tree"],
        circle_color="#EC0000",
        path_color="#FFFFFF",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
