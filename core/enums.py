from enum import Enum


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Module(ChoicesEnum):
    CONSTRUCTION_WORK = "construction-work"


class NotificationType(ChoicesEnum):
    CONSTRUCTION_WORK_WARNING_MESSAGE = (
        f"{Module.CONSTRUCTION_WORK.value}:warning-message"
    )
