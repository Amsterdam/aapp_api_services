from collections import defaultdict
from enum import Enum
from typing import NamedTuple


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Module(ChoicesEnum):
    CONSTRUCTION_WORK = "construction-work"
    PARKING = "parking"
    WASTE = "waste-guide"
    MIJN_AMS = "mijn-amsterdam"
    CITY_PASS = "city-pass"
    BURNING_GUIDE = "burning-guide"

    @property
    def notification_description(self):
        descriptions = {
            Module.CONSTRUCTION_WORK: "Nieuws van projecten die u volgt.",
            Module.PARKING: "Herinnering dat een parkeersessie afloopt of uw saldo bijna op is.",
            Module.WASTE: "Herinnering buitenzetten container en actuele meldingen (wijzigingen en vertragingen).",
            Module.MIJN_AMS: "Blijf op de hoogte van uw aanvragen of klachten.",
            Module.CITY_PASS: "Over uw saldo, regelingen en tips.",
            Module.BURNING_GUIDE: "U ontvangt meldingen als het code rood is voor 'Mijn adres'.",
        }
        return descriptions[self]


class NotificationTypeClass(NamedTuple):
    module: Module
    name: str
    description: str

    def __str__(self):
        return f"{self.module.value}:{self.name}"


class NotificationType(ChoicesEnum):
    CONSTRUCTION_WORK_WARNING_MESSAGE = NotificationTypeClass(
        module=Module.CONSTRUCTION_WORK,
        name="warning-message",
        description="Nieuws van projecten die u volgt",
    )
    PARKING_REMINDER = NotificationTypeClass(
        module=Module.PARKING,
        name="parking-reminder",
        description="Parkeersessie loopt af",
    )
    WASTE_DATE_REMINDER = NotificationTypeClass(
        module=Module.WASTE,
        name="date-reminder",
        description="Herinnering buitenzetten container",
    )
    WASTE_MANUAL_NOTIFICATION = NotificationTypeClass(
        module=Module.WASTE,
        name="manual-notification",
        description="A&G meldingen over afvalinzameling",
    )
    MIJN_AMS_BELASTING = NotificationTypeClass(
        module=Module.MIJN_AMS,
        name="belasting",
        description="Nieuwe berichten over belasting",
    )
    CITY_PASS_NOTIFICATION = NotificationTypeClass(
        module=Module.CITY_PASS,
        name="notification",
        description="Nieuws over regelingen",
    )
    BURNING_GUIDE_NOTIFICATION = NotificationTypeClass(
        module=Module.BURNING_GUIDE,
        name="notification",
        description="U ontvangt meldingen als het code rood is voor 'Mijn adres'",
    )

    @property
    def value(self):
        if str(self._value_) == "construction-work:warning-message":
            return "ProjectWarningCreatedByProjectManager"
        return str(self._value_)

    @classmethod
    def get_modules_with_types_and_descriptions(cls):
        """Get modules with their notification types, only including modules that have types."""
        # Group notification types by module
        module_types = defaultdict(list)

        for notification_type in cls:
            module_types[notification_type._value_.module].append(
                {
                    "type": notification_type.value,
                    "description": notification_type._value_.description,
                }
            )

        # Build the result, only including modules that have notification types
        result = []
        for module, types in module_types.items():
            result.append(
                {
                    "module": module.value,
                    "description": module.notification_description,
                    "types": types,
                }
            )

        return result
