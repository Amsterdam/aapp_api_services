from enum import Enum


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Module(ChoicesEnum):
    CONSTRUCTION_WORK = "construction-work"
    PARKING = "parking"
    WASTE = "waste"


class NotificationType(ChoicesEnum):
    CONSTRUCTION_WORK_WARNING_MESSAGE = (
        f"{Module.CONSTRUCTION_WORK.value}:warning-message"
    )
    PARKING_REMINDER = f"{Module.PARKING.value}:parking-reminder"
    WASTE_DATE_REMINDER = f"{Module.WASTE.value}:date-reminder"
