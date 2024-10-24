import enum


class ManagerType(enum.Enum):
    EDITOR = "editor"
    PUBLISHER = "publisher"
    EDITOR_PUBLISHER = "editor_publisher"
    NOT_FOUND = "not_found"

    def is_editor(self) -> bool:
        return self in [ManagerType.EDITOR, ManagerType.EDITOR_PUBLISHER]

    def is_publisher(self) -> bool:
        return self in [ManagerType.PUBLISHER, ManagerType.EDITOR_PUBLISHER]
