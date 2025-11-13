import enum


class ManagerType(enum.Enum):
    EDITOR = "editor"
    PUBLISHER = "publisher"
    NOT_FOUND = "not_found"

    def is_editor(self) -> bool:
        return self == ManagerType.EDITOR

    def is_publisher(self) -> bool:
        return self == ManagerType.PUBLISHER
