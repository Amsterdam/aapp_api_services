from enum import Enum


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Module(ChoicesEnum):
    CONSTRUCTION_WORK = "construction-work"
    PARKING = "parking"
    WASTE = "waste"
    MIJN_AMS = "mijn-amsterdam"
    CITY_PASS = "city-pass"


class NotificationType(ChoicesEnum):
    CONSTRUCTION_WORK_WARNING_MESSAGE = (
        f"{Module.CONSTRUCTION_WORK.value}:warning-message"
    )
    PARKING_REMINDER = f"{Module.PARKING.value}:parking-reminder"
    WASTE_DATE_REMINDER = f"{Module.WASTE.value}:date-reminder"
    MIJN_AMS_NOTIFICATION = f"{Module.MIJN_AMS.value}:notification"
    CITY_PASS_NOTIFICATION = f"{Module.CITY_PASS.value}:notification"
